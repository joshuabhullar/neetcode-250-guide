#!/usr/bin/env python3
"""
Generate a NeetCode study plan that includes ALL 250 problems over a configurable
number of days (default 125). Uses same category per day with spaced repetition
and intelligent category ordering.
"""

import argparse
import json
import os
import random
from datetime import datetime, timedelta
from collections import defaultdict, deque

DIFFICULTIES = ['Easy', 'Medium', 'Hard']

def load_problems():
    """Load all 250 problems from JSON file."""
    with open('neetcode_250_complete.json', 'r', encoding='utf-8') as f:
        data = json.load(f)
    return data['problems']

def organize_problems_by_category_and_difficulty(problems):
    """Organize problems by category and difficulty."""
    category_problems = defaultdict(lambda: {'Easy': [], 'Medium': [], 'Hard': []})

    for problem in problems:
        category = problem['category']
        difficulty = problem['difficulty']
        category_problems[category][difficulty].append(problem)

    return category_problems

def get_phase_boundaries(total_days):
    """
    Scale the original 125-day phase boundaries (days 30 and 80) to the plan length.
    Returns (early_end, middle_end) as day counts.
    """
    early_end = round(total_days * 30 / 125)
    middle_end = round(total_days * 80 / 125)
    return early_end, middle_end

def build_daily_quotas(total_problems, total_days):
    """
    Spread problems across days as evenly as possible. Heavier days come first so the
    final stretch (Medium/Hard-heavy) gets fewer problems per day.
    """
    base, extra = divmod(total_problems, total_days)
    return [base + 1 if day < extra else base for day in range(total_days)]

def count_remaining(category, category_problems, used_problems):
    """Count problems in a category that have not been scheduled yet."""
    return sum(
        1
        for difficulty in DIFFICULTIES
        for problem in category_problems[category][difficulty]
        if problem['name'] not in used_problems
    )

def calculate_category_weights(day, total_days, category_order, category_problems, category_usage_history, used_problems):
    """
    Calculate weights for category selection based on:
    1. Day progression (easier categories get higher weight early)
    2. Spaced repetition (categories used recently get lower weight)
    3. Category availability (categories with remaining problems)
    """
    weights = {}

    # Base weight based on category difficulty order and day progression
    for i, category in enumerate(category_order):
        # Early days favor easier categories, later days favor harder ones
        position_in_order = i / len(category_order)
        day_progress = day / total_days

        # Calculate base weight based on category difficulty and day
        if day_progress < 0.25:  # First 25% of days
            base_weight = 1.0 - (position_in_order * 0.8)  # Heavily favor early categories
        elif day_progress < 0.5:  # Second 25% of days
            base_weight = 1.0 - (position_in_order * 0.6)  # Moderate favor to early categories
        elif day_progress < 0.75:  # Third 25% of days
            base_weight = 0.3 + (position_in_order * 0.5)  # Gradual transition to later categories
        else:  # Final 25% of days
            base_weight = position_in_order + 0.2  # Favor later categories

        remaining_problems = count_remaining(category, category_problems, used_problems)

        # Boost weight if category has many remaining problems
        if remaining_problems > 4:
            base_weight *= 1.2
        elif remaining_problems == 0:
            base_weight = 0  # No problems left

        weights[category] = max(0.05, base_weight)  # Minimum weight of 0.05

    # Apply spaced repetition penalty
    recent_usage_penalty = 0.6
    for i, recent_category in enumerate(category_usage_history):
        if i < 6:  # Last 6 uses get penalty (more recent = higher penalty)
            penalty = recent_usage_penalty * (1 - i/6)
            if recent_category in weights:
                weights[recent_category] = max(0.02, weights[recent_category] - penalty)

    return weights

def select_category_for_day(quota, category_order, category_problems, category_weights, used_problems):
    """
    Select a single category for the day. Prefers categories that can fill the whole
    daily quota, then falls back to categories with fewer problems left.
    """
    remaining = {cat: count_remaining(cat, category_problems, used_problems) for cat in category_order}

    for minimum in range(quota, 0, -1):
        available_categories = [cat for cat in category_order if remaining[cat] >= minimum]
        if available_categories:
            break
    else:
        return None

    # Weight-based selection from available categories
    available_weights = [category_weights.get(cat, 0.05) for cat in available_categories]
    total_weight = sum(available_weights)
    if total_weight > 0:
        probabilities = [w/total_weight for w in available_weights]
        return random.choices(available_categories, weights=probabilities)[0]
    return random.choice(available_categories)

def get_difficulty_preferences(day, early_end, middle_end):
    """Difficulty preference for each problem slot of the day, based on plan phase."""
    if day < early_end:  # Early phase: mostly easy with some medium
        return [
            ['Easy', 'Medium', 'Hard'],
            ['Easy', 'Easy', 'Medium'] if day % 3 != 0 else ['Medium', 'Easy', 'Hard'],
            ['Medium', 'Easy', 'Hard'],
        ]
    elif day < middle_end:  # Middle phase: mix of easy/medium with some hard
        return [
            ['Easy', 'Medium', 'Hard'],
            ['Medium', 'Easy', 'Hard'],
            ['Medium', 'Hard', 'Easy'],
        ]
    else:  # Final phase: more medium/hard
        return [
            ['Medium', 'Hard', 'Easy'],
            ['Medium', 'Hard', 'Easy'],
            ['Hard', 'Medium', 'Easy'],
        ]

def pick_problem(category, difficulty_order, category_problems, used_problems):
    """Pick the first unused problem in a category, following the difficulty order."""
    for difficulty in difficulty_order:
        for problem in category_problems[category][difficulty]:
            if problem['name'] not in used_problems:
                used_problems.add(problem['name'])
                return problem
    return None

def select_problems_for_day(day, quota, selected_category, category_problems, category_weights,
                            used_problems, early_end, middle_end):
    """
    Select `quota` problems for the day, from the selected category when possible.
    If the category runs out, top up from the next highest-weighted categories.
    """
    difficulty_preferences = get_difficulty_preferences(day, early_end, middle_end)
    day_problems = []

    def preference_for(slot):
        return difficulty_preferences[slot] if slot < len(difficulty_preferences) else DIFFICULTIES

    while len(day_problems) < quota:
        problem = pick_problem(selected_category, preference_for(len(day_problems)), category_problems, used_problems)
        if not problem:
            break
        day_problems.append(problem)

    fallback_categories = sorted(
        (cat for cat in category_weights if cat != selected_category),
        key=lambda cat: category_weights[cat],
        reverse=True,
    )
    for category in fallback_categories:
        while len(day_problems) < quota:
            problem = pick_problem(category, preference_for(len(day_problems)), category_problems, used_problems)
            if not problem:
                break
            day_problems.append(problem)

    return day_problems

def generate_study_plan(problems, start_date, total_days):
    """Generate a `total_days`-day plan that includes ALL problems."""

    # Define category order (from easiest to hardest)
    category_order = [
        "Arrays & Hashing",
        "Two Pointers",
        "Sliding Window",
        "Stack",
        "Binary Search",
        "Linked List",
        "Trees",
        "Heap / Priority Queue",
        "Backtracking",
        "Tries",
        "Graphs",
        "Advanced Graphs",
        "1-D Dynamic Programming",
        "2-D Dynamic Programming",
        "Greedy",
        "Intervals",
        "Math & Geometry",
        "Bit Manipulation"
    ]

    category_problems = organize_problems_by_category_and_difficulty(problems)
    quotas = build_daily_quotas(len(problems), total_days)
    early_end, middle_end = get_phase_boundaries(total_days)

    plan = []
    used_problems = set()
    category_usage_history = deque(maxlen=10)  # Track recent category usage

    for day, quota in enumerate(quotas):
        current_date = start_date + timedelta(days=day)

        category_weights = calculate_category_weights(
            day, total_days, category_order, category_problems, category_usage_history, used_problems
        )
        selected_category = select_category_for_day(
            quota, category_order, category_problems, category_weights, used_problems
        )
        if not selected_category:
            print(f"Warning: No problems left on day {day + 1}")
            break

        day_problems = select_problems_for_day(
            day, quota, selected_category, category_problems, category_weights,
            used_problems, early_end, middle_end
        )

        categories = {p['category'] for p in day_problems}
        plan.append({
            'date': current_date.strftime('%Y-%m-%d'),
            'day': day + 1,
            'problems': day_problems,
            'category': selected_category if len(categories) == 1 else "Mixed"
        })

        # Update category usage history
        if selected_category in category_usage_history:
            category_usage_history.remove(selected_category)
        category_usage_history.appendleft(selected_category)

    return plan

def analyze_plan_distribution(plan, total_days):
    """Analyze the distribution of categories and difficulties throughout the plan."""
    early_end, middle_end = get_phase_boundaries(total_days)
    phases = [
        f'Early (1-{early_end})',
        f'Middle ({early_end + 1}-{middle_end})',
        f'Late ({middle_end + 1}-{total_days})',
    ]

    category_by_phase = {phase: defaultdict(int) for phase in phases}
    difficulty_by_phase = {phase: defaultdict(int) for phase in phases}
    category_progression = []

    for day_plan in plan:
        day_num = day_plan['day']
        problems = day_plan['problems']
        category = day_plan.get('category', 'Unknown')

        # Track category progression
        category_progression.append((day_num, category))

        # Determine phase
        if day_num <= early_end:
            phase = phases[0]
        elif day_num <= middle_end:
            phase = phases[1]
        else:
            phase = phases[2]

        # Track categories and difficulties
        category_by_phase[phase][category] += 1
        for problem in problems:
            difficulty_by_phase[phase][problem['difficulty']] += 1

    return category_by_phase, difficulty_by_phase, category_progression

def describe_daily_load(plan):
    """Describe how many problems per day, e.g. '3 problems/day for days 1-70, 2 problems/day for days 71-90'."""
    segments = []
    for day_plan in plan:
        count = len(day_plan['problems'])
        if segments and segments[-1][0] == count:
            segments[-1][2] = day_plan['day']
        else:
            segments.append([count, day_plan['day'], day_plan['day']])

    if len(segments) == 1:
        return f"{segments[0][0]} problems per day for {len(plan)} days"
    return ", ".join(f"{count} problems/day for days {start}-{end}" for count, start, end in segments)

def generate_markdown_plan(plan):
    """Generate markdown for the study plan."""
    total_days = len(plan)
    total_problems = sum(len(day['problems']) for day in plan)
    markdown = f"# NeetCode 250 - Complete {total_days}-Day Study Plan (All {total_problems} Problems)\n\n"
    markdown += f"**Schedule:** {plan[0]['date']} to {plan[-1]['date']}\n\n"
    markdown += "**Enhanced Study Strategy:**\n"
    markdown += f"- {describe_daily_load(plan)} (same category each day when possible)\n"
    markdown += f"- ALL {total_problems} problems included with no gaps\n"
    markdown += "- Spaced repetition: Categories cycle with intelligent spacing to optimize retention\n"
    markdown += "- Progressive difficulty: Early days focus on Easy, gradually increasing complexity\n"
    markdown += "- Category focus: Daily concentration on single topics for deeper pattern recognition\n"
    markdown += "- Intelligent timing: Easier categories appear earlier, advanced topics later in the plan\n\n"
    markdown += "---\n\n"

    for day_plan in plan:
        date = day_plan['date']
        day_num = day_plan['day']
        problems = day_plan['problems']
        category = day_plan.get('category', 'Mixed')

        markdown += f"## Day {day_num} - {date}\n"
        markdown += f"**Topic:** {category}\n\n"
        markdown += "**Problems:**\n"

        for problem in problems:
            difficulty_emoji = {"Easy": "🟢", "Medium": "🟡", "Hard": "🔴"}[problem['difficulty']]
            markdown += f"- [ ] {difficulty_emoji} [{problem['name']}]({problem['leetcode_url']}) - *{problem['category']}*\n"

        markdown += "\n"

    return markdown

def next_monday():
    today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    days_ahead = 0 - today.weekday()  # Monday is 0
    if days_ahead <= 0:  # Target day already happened this week
        days_ahead += 7
    return today + timedelta(days=days_ahead)

def parse_start_date(date_input):
    """Parse 'today', 'monday', '' (next Monday), or YYYY-MM-DD. Raises ValueError on bad input."""
    date_input = date_input.strip().lower()
    if date_input == '' or date_input == 'monday':
        return next_monday()
    if date_input == 'today':
        return datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    return datetime.strptime(date_input, '%Y-%m-%d')

def get_start_date(total_days):
    """Get the start date from user input."""
    print(f"📅 When would you like to start your {total_days}-day study plan?")
    print("Examples:")
    print("  - 2025-01-01 (New Year)")
    print("  - today (starts today)")
    print("  - monday (starts next Monday)")
    print("  - Press Enter for default (next Monday)")

    while True:
        try:
            date_input = input("\nEnter start date (YYYY-MM-DD, 'today', 'monday', or Enter for default): ")
            return parse_start_date(date_input)
        except ValueError:
            print("❌ Invalid date format. Please use YYYY-MM-DD, 'today', 'monday', or press Enter for default")
            continue
        except (EOFError, KeyboardInterrupt):
            # Handle non-interactive environments or Ctrl+C
            print("\n📅 Using default start date (next Monday)")
            return next_monday()

def parse_args():
    parser = argparse.ArgumentParser(description="Generate a NeetCode 250 study plan.")
    parser.add_argument('--days', type=int, default=125,
                        help="Number of days in the plan (default: 125)")
    parser.add_argument('--start',
                        help="Start date: YYYY-MM-DD, 'today', or 'monday'. Prompts if omitted.")
    parser.add_argument('--seed', type=int,
                        help="Random seed for a reproducible plan")
    args = parser.parse_args()

    if not 1 <= args.days <= 250:
        parser.error("--days must be between 1 and 250")
    if args.start is not None:
        try:
            args.start = parse_start_date(args.start)
        except ValueError:
            parser.error("--start must be YYYY-MM-DD, 'today', or 'monday'")
    return args

def main():
    args = parse_args()
    total_days = args.days

    print(f"🔧 Generating {total_days}-day plan with ALL 250 problems...")

    if args.seed is not None:
        random.seed(args.seed)

    start_date = args.start or get_start_date(total_days)
    print(f"📅 Study plan will start on: {start_date.strftime('%A, %B %d, %Y')}")

    # Load all problems
    all_problems = load_problems()
    print(f"📚 Loaded {len(all_problems)} total problems")

    print(f"\n🗓️ Generating complete plan...")
    plan = generate_study_plan(all_problems, start_date, total_days)

    # Count total problems in plan
    total_problems_in_plan = sum(len(day['problems']) for day in plan)
    print(f"\n✅ Plan includes {total_problems_in_plan} problems out of 250 total")

    if total_problems_in_plan < 250:
        print(f"❌ WARNING: Missing {250 - total_problems_in_plan} problems!")
        return

    # Analyze distribution
    print(f"\n📊 Analyzing plan distribution...")
    category_by_phase, difficulty_by_phase, category_progression = analyze_plan_distribution(plan, total_days)

    # Generate markdown
    markdown_content = generate_markdown_plan(plan)

    # Check if file already exists and find next available filename
    base_filename = f'NeetCode_250_Study_Plan_{start_date.strftime("%Y-%m-%d")}'
    if total_days != 125:
        base_filename = f'NeetCode_250_Study_Plan_{total_days}_Days_{start_date.strftime("%Y-%m-%d")}'
    filename = f'{base_filename}.md'
    counter = 1

    while os.path.exists(filename):
        filename = f'{base_filename}_{counter}.md'
        counter += 1

    # Save to file
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(markdown_content)

    print(f"✅ Generated complete {total_days}-day plan with {len(plan)} days")
    print(f"📄 Saved to: {filename}")

    # Summary statistics
    print(f"\n📈 Plan Statistics:")
    print(f"  Total days: {len(plan)}")
    print(f"  Dates: {plan[0]['date']} to {plan[-1]['date']}")
    print(f"  Total problems: {total_problems_in_plan}")
    print(f"  Average problems per day: {total_problems_in_plan / len(plan):.1f}")
    print(f"  Daily load: {describe_daily_load(plan)}")

    # Category focus statistics
    same_category_days = sum(1 for day in plan if day.get('category') != 'Mixed')
    mixed_category_days = len(plan) - same_category_days

    print(f"\n🎯 Category Focus:")
    print(f"  Same category days: {same_category_days} ({same_category_days/len(plan)*100:.1f}%)")
    print(f"  Mixed category days: {mixed_category_days} ({mixed_category_days/len(plan)*100:.1f}%)")

    # Difficulty distribution by phase
    print(f"\n📊 Difficulty Distribution by Phase:")
    for phase, difficulties in difficulty_by_phase.items():
        total_phase = sum(difficulties.values())
        if total_phase > 0:
            print(f"  {phase}:")
            for diff, count in difficulties.items():
                percentage = (count / total_phase) * 100
                print(f"    {diff}: {count} ({percentage:.1f}%)")

    # Verify all problems are included
    used_problem_names = set()
    for day in plan:
        for problem in day['problems']:
            used_problem_names.add(problem['name'])

    all_problem_names = set(p['name'] for p in all_problems)
    missing_problems = all_problem_names - used_problem_names

    if missing_problems:
        print(f"\n❌ Missing Problems ({len(missing_problems)}):")
        for problem in sorted(missing_problems):
            print(f"  - {problem}")
    else:
        print(f"\n✅ All 250 problems successfully included!")

if __name__ == "__main__":
    main()
