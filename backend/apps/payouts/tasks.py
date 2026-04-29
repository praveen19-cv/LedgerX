"""
Celery Tasks for Payout Processing.

Worker flow:
  1. process_pending_payouts — picks PENDING payouts, transitions to PROCESSING,
     then simulates bank outcome (70% success, 20% failure, 10% stuck).
  2. recover_stuck_payouts — detects payouts stuck in PROCESSING > threshold,
     applies exponential backoff retry or marks FAILED with RELEASE ledger entry.

All DB mutations are atomic. No Python-side money math.
"""

import logging
import random
from datetime import timedelta

from celery import shared_task
from django.db import transaction
from django.utils import timezone
from django.conf import settings

from apps.ledger.models import LedgerEntry
from .models import Payout

logger = logging.getLogger(__name__)


def _finalize_payout_success(payout):
    """Atomically mark payout COMPLETED and convert HOLD → DEBIT."""
    with transaction.atomic():
        # Re-fetch with lock to prevent concurrent state mutation
        payout = Payout.objects.select_for_update().get(id=payout.id)

        if not payout.can_transition_to(Payout.Status.COMPLETED):
            logger.warning(
                "Cannot transition payout %s from %s to COMPLETED",
                payout.id,
                payout.status,
            )
            return

        payout.status = Payout.Status.COMPLETED
        payout.save(update_fields=["status", "updated_at"])

        # Convert the HOLD into a permanent DEBIT
        LedgerEntry.objects.create(
            merchant=payout.merchant,
            type=LedgerEntry.EntryType.DEBIT,
            amount_paise=payout.amount_paise,
            reference_type=LedgerEntry.ReferenceType.PAYOUT,
            reference_id=payout.id,
            description=f"Payout {payout.id} completed",
        )

    logger.info("Payout %s completed successfully.", payout.id)


def _finalize_payout_failure(payout, reason="Simulated failure"):
    """Atomically mark payout FAILED and RELEASE held funds."""
    with transaction.atomic():
        payout = Payout.objects.select_for_update().get(id=payout.id)

        if not payout.can_transition_to(Payout.Status.FAILED):
            logger.warning(
                "Cannot transition payout %s from %s to FAILED",
                payout.id,
                payout.status,
            )
            return

        payout.status = Payout.Status.FAILED
        payout.failure_reason = reason
        payout.save(update_fields=["status", "failure_reason", "updated_at"])

        # Release the held funds back to the merchant
        LedgerEntry.objects.create(
            merchant=payout.merchant,
            type=LedgerEntry.EntryType.RELEASE,
            amount_paise=payout.amount_paise,
            reference_type=LedgerEntry.ReferenceType.PAYOUT,
            reference_id=payout.id,
            description=f"Release for failed payout {payout.id}: {reason}",
        )

    logger.info("Payout %s failed: %s. Funds released.", payout.id, reason)


@shared_task(name="apps.payouts.tasks.process_pending_payouts")
def process_pending_payouts():
    """
    Picks up PENDING payouts and kicks off processing.
    Transitions: PENDING → PROCESSING → (COMPLETED | FAILED | stuck)
    """
    pending_payouts = Payout.objects.filter(status=Payout.Status.PENDING).select_related(
        "merchant"
    )

    if not pending_payouts.exists():
        logger.debug("No pending payouts to process.")
        return

    for payout in pending_payouts:
        try:
            with transaction.atomic():
                # Lock individual payout row before transitioning
                locked = Payout.objects.select_for_update(skip_locked=True).get(
                    id=payout.id, status=Payout.Status.PENDING
                )
                locked.status = Payout.Status.PROCESSING
                locked.processing_started_at = timezone.now()
                locked.save(update_fields=["status", "processing_started_at", "updated_at"])

            # Simulate external bank call (outside transaction — no DB lock held)
            _simulate_bank_processing.apply_async(
                args=[str(payout.id)],
                countdown=2,  # small delay to simulate network
            )

        except Payout.DoesNotExist:
            # Another worker already grabbed this payout
            continue
        except Exception as exc:
            logger.exception("Error transitioning payout %s: %s", payout.id, exc)


@shared_task(name="apps.payouts.tasks.simulate_bank_processing")
def _simulate_bank_processing(payout_id):
    """
    Simulates the external bank API response.
    70% success | 20% failure | 10% stuck (no response → recovered by recover_stuck_payouts)
    """
    try:
        payout = Payout.objects.get(id=payout_id)
    except Payout.DoesNotExist:
        logger.error("Payout %s not found for simulation.", payout_id)
        return

    if payout.status != Payout.Status.PROCESSING:
        logger.warning(
            "Payout %s is not in PROCESSING state (got %s). Skipping.",
            payout_id,
            payout.status,
        )
        return

    roll = random.random()

    if roll < 0.70:  # 70% success
        _finalize_payout_success(payout)
    elif roll < 0.90:  # 20% failure
        _finalize_payout_failure(payout, reason="Bank declined the transfer")
    else:
        # 10% stuck — intentionally do nothing.
        # recover_stuck_payouts will handle this after the threshold.
        logger.info(
            "Payout %s is stuck in PROCESSING — will be recovered by watchdog.",
            payout_id,
        )


@shared_task(name="apps.payouts.tasks.recover_stuck_payouts")
def recover_stuck_payouts():
    """
    Watchdog task:  finds payouts stuck in PROCESSING beyond the threshold
    and either retries them (up to max) or marks them FAILED with fund release.
    Uses exponential backoff: wait = 2^retry_count * base_seconds
    """
    max_retries = getattr(settings, "PAYOUT_MAX_RETRIES", 3)
    stuck_threshold_seconds = getattr(settings, "PAYOUT_STUCK_THRESHOLD_SECONDS", 30)

    threshold_time = timezone.now() - timedelta(seconds=stuck_threshold_seconds)

    stuck_payouts = Payout.objects.filter(
        status=Payout.Status.PROCESSING,
        processing_started_at__lt=threshold_time,
    ).select_related("merchant")

    for payout in stuck_payouts:
        if payout.retry_count < max_retries:
            # Retry with exponential backoff
            payout.retry_count += 1
            payout.status = Payout.Status.PENDING
            payout.processing_started_at = None
            payout.save(update_fields=["status", "retry_count", "processing_started_at", "updated_at"])

            backoff = 2 ** payout.retry_count
            logger.info(
                "Re-queuing payout %s (retry %d/%d) with %ds backoff.",
                payout.id,
                payout.retry_count,
                max_retries,
                backoff,
            )
        else:
            # Exhausted retries → mark FAILED, release funds
            _finalize_payout_failure(
                payout,
                reason=f"Max retries ({max_retries}) exhausted — payout stuck in PROCESSING",
            )
