#!/usr/bin/env python3
"""
Demo: LinkedIn Automation Phase 1 & 2

This demo shows:
1. Human behavior patterns
2. Session management
3. Rate limiting
4. Realistic timing

Run: python demo_phase1_phase2.py
"""

import asyncio
import random
from datetime import datetime
from app.services.linkedin.human_behavior import HumanBehaviorEngine


def print_header(title: str):
    """Print a section header."""
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70)


def print_metric(label: str, value: str, indent: int = 2):
    """Print a metric with formatting."""
    spaces = " " * indent
    print(f"{spaces}• {label}: {value}")


async def demo_human_behavior():
    """Demonstrate human behavior patterns."""
    print_header("HUMAN BEHAVIOR ENGINE DEMO")

    behavior = HumanBehaviorEngine()

    # 1. Profile Dwell Times
    print("\n📱 Profile Dwell Times")
    print("   (How long humans spend reading profiles)")
    print()

    for complexity in ['simple', 'medium', 'complex']:
        dwell = behavior.get_profile_dwell_time(complexity)
        print_metric(
            f"{complexity.capitalize()} profile",
            f"{dwell:.1f} seconds"
        )

    # 2. Message Timing
    print("\n💬 Message Send Delays")
    print("   (Random delays between 30s-5min, skewed toward 90s)")
    print()

    delays = [behavior.get_delay_between_messages() for _ in range(5)]
    for i, delay in enumerate(delays, 1):
        minutes = delay / 60
        print_metric(
            f"Message {i}",
            f"{delay:.0f}s ({minutes:.1f} min)"
        )

    # 3. Session Management
    print("\n⏰ Session Management")
    print()

    behavior.start_session()
    print_metric("Session started", datetime.now().strftime("%H:%M:%S"))
    print_metric(
        "Will run for",
        f"{random.randint(45, 90)} minutes"
    )
    print_metric(
        "Then break for",
        f"{random.randint(120, 360)} minutes"
    )

    # 4. Working Hours
    print("\n🕐 Working Hours & Rate Limiting")
    print()

    is_working = behavior.is_working_hours()
    is_weekday = behavior.is_weekday()
    now = datetime.now()

    print_metric("Current time", now.strftime("%A, %I:%M %p"))
    print_metric("Working hours?", "✅ Yes" if is_working else "❌ No (8am-8pm only)")
    print_metric("Weekday?", "✅ Yes" if is_weekday else "❌ No (Mon-Fri only)")

    # Check rate limits
    print("\n📊 Rate Limit Checks")
    print()

    scenarios = [
        (10, 50, "Under daily limit"),
        (50, 50, "At daily limit"),
        (60, 50, "Over daily limit")
    ]

    for sent, limit, description in scenarios:
        can_send, reason = behavior.should_send_message(sent, limit)
        status = "✅ Can send" if can_send else f"❌ Blocked"
        details = f"({sent}/{limit} messages)"

        if not can_send and reason:
            details = f"{details} - {reason}"

        print_metric(description, f"{status} {details}")


async def demo_connection_extraction():
    """Demonstrate connection extraction behavior."""
    print_header("CONNECTION EXTRACTION SIMULATION")

    print("\n📜 Extracting connections with human-like behavior")
    print("   • Smooth scrolling (8-15 steps per scroll)")
    print("   • 1-3 second delays between scrolls")
    print("   • 10% chance to scroll back up (re-reading)")
    print()

    behavior = HumanBehaviorEngine()
    behavior.start_session()

    total_connections = random.randint(800, 1200)
    extracted = 0
    scroll_count = 0

    print(f"🎯 Target: ~{total_connections} connections\n")

    while extracted < total_connections:
        scroll_count += 1

        # Simulate extracting 40-60 connections per scroll
        new_connections = random.randint(40, 60)
        extracted = min(extracted + new_connections, total_connections)

        # Progress bar
        progress = (extracted / total_connections) * 100
        bar_length = 30
        filled = int(bar_length * extracted / total_connections)
        bar = "█" * filled + "░" * (bar_length - filled)

        # Scroll delay
        delay = random.uniform(1.0, 3.0)

        print(f"   Scroll {scroll_count:2d}: {bar} {progress:5.1f}% | {extracted:4d}/{total_connections} | delay: {delay:.2f}s", end="")

        # Occasionally show back-scroll
        if random.random() < 0.1:
            print(" 📖 (back-scroll)")
        else:
            print()

        # Actually wait
        await asyncio.sleep(delay)

        # Check for session break
        if scroll_count > 20 and behavior.should_take_break():
            print(f"\n   ⏸️  Session limit reached after {scroll_count} scrolls")
            break_duration = behavior.get_break_duration()
            print(f"       Would take {break_duration // 60} minute break\n")
            break

    duration = scroll_count * 2.0  # Average 2s per scroll
    print(f"\n✅ Extraction complete!")
    print(f"   • Extracted: {extracted} connections")
    print(f"   • Scrolls: {scroll_count}")
    print(f"   • Duration: ~{duration:.0f} seconds ({duration/60:.1f} minutes)")


async def demo_message_typing():
    """Demonstrate realistic message typing."""
    print_header("MESSAGE TYPING SIMULATION")

    print("\n⌨️  Typing with human-like behavior:")
    print("   • 40-80 WPM with variance")
    print("   • Occasional typos + backspace")
    print("   • Natural pauses between words")
    print()

    message = "Hi Sarah! I noticed your ML work at Stripe. We're hiring!"

    behavior = HumanBehaviorEngine()
    wpm = random.uniform(40, 80)

    print(f"💬 Message: \"{message}\"")
    print(f"⚡ Speed: {wpm:.0f} WPM\n")

    # Calculate typing time
    words = len(message.split())
    base_time = (words / wpm) * 60
    with_variance = base_time * random.uniform(1.1, 1.3)  # Add variance

    print(f"   Typing", end="", flush=True)

    # Simulate typing with dots
    for i in range(10):
        await asyncio.sleep(with_variance / 10)
        print(".", end="", flush=True)

    print(f" done! ({with_variance:.1f}s)")

    # Show occasional typo
    if random.random() < 0.3:
        print(f"   💭 Oops! Typo detected → backspace → retype (+{random.uniform(0.5, 1.0):.1f}s)")


async def main():
    """Run all demos."""
    print("\n")
    print("╔═════════════════════════════════════════════════════════════════════╗")
    print("║                                                                     ║")
    print("║         LinkedIn Automation - Phase 1 & 2 Demo                     ║")
    print("║         Human-Like Behavior Patterns                                ║")
    print("║                                                                     ║")
    print("╚═════════════════════════════════════════════════════════════════════╝")

    # Run demos
    await demo_human_behavior()
    await demo_connection_extraction()
    await demo_message_typing()

    # Final summary
    print_header("SUMMARY")
    print()
    print("✅ Phase 1: Credential Authentication")
    print("   • Direct login with email/password")
    print("   • 2FA support")
    print("   • Cookie extraction & encryption")
    print()
    print("✅ Phase 2: Connection Extraction")
    print("   • Comet-style human behavior")
    print("   • Smooth scrolling with delays")
    print("   • Session management with breaks")
    print("   • Rate limiting & working hours")
    print()
    print("📊 Behavior Metrics:")
    print_metric("Profile dwell", "20-60s (based on complexity)")
    print_metric("Scroll delay", "1-3s between scrolls")
    print_metric("Session length", "45-90 minutes")
    print_metric("Break duration", "2-6 hours")
    print_metric("Message typing", "40-80 WPM with typos")
    print_metric("Working hours", "8am-8pm, weekdays only")
    print()
    print("🔧 Next Steps:")
    print_metric("Phase 3", "Smart prioritization algorithm")
    print_metric("Phase 4", "Profile enrichment via scraper pool")
    print_metric("Phase 5", "DM automation with approval")
    print()
    print("=" * 70)
    print()


if __name__ == '__main__':
    asyncio.run(main())
