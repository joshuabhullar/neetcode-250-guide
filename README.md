# NeetCode 250 Study Plan Generator

A Python-based tool that generates an optimized 125-day study plan covering all 250 NeetCode problems for coding interview preparation.

## 🚀 Features

- **Complete Coverage**: Includes all 250 NeetCode problems with no gaps
- **Personalized Start Date**: Choose when to begin your study journey
- **Intelligent Scheduling**: 2 problems per day from the same category when possible
- **Spaced Repetition**: Categories cycle with intelligent spacing to optimize retention
- **Progressive Difficulty**: Early days focus on Easy problems, gradually increasing complexity
- **Category Focus**: Daily concentration on single topics for deeper pattern recognition
- **Smart Timing**: Easier categories appear earlier, advanced topics later in the plan

## 📋 Generated Study Plan

The generated plan includes:
- **125 days** of structured learning
- **18 problem categories** covering all major algorithmic concepts
- **Difficulty progression** from Easy → Medium → Hard
- **Checkboxes** for tracking progress
- **Direct links** to LeetCode problems

### Problem Categories
- Arrays & Hashing
- Two Pointers
- Sliding Window
- Stack
- Binary Search
- Linked List
- Trees
- Heap / Priority Queue
- Backtracking
- Tries
- Graphs
- Advanced Graphs
- 1-D Dynamic Programming
- 2-D Dynamic Programming
- Greedy
- Intervals
- Math & Geometry
- Bit Manipulation

## 🛠️ Usage

### Generate Study Plan
```bash
python3 generate_study_plan.py
```

The script will prompt you to choose when to start your study plan:
- **Specific date**: Enter `2025-01-01` or any YYYY-MM-DD format
- **Start today**: Enter `today`
- **Start next Monday**: Enter `monday` or just press Enter for default
- **Interactive examples**: The script provides helpful examples and validation

This creates `NeetCode_250_Study_Plan_<start-date>.md` with your personalized study schedule.

### Custom Plan Length
```bash
# 90-day plan starting Oct 1, 2026 (3 problems/day for days 1-70, 2/day for days 71-90)
python3 generate_study_plan.py --days 90 --start 2026-10-01 --seed 3

# Roadmap order: finish each topic before moving on (recommended)
python3 generate_study_plan.py --days 90 --start 2026-10-01 --order roadmap \
  --output NeetCode_250_Study_Plan_90_Days_2026-10-01.md \
  --completed "Contains Duplicate" "Valid Anagram" "Two Sum"
```

- `--days N` - spread all 250 problems over N days (default 125). Problems are split as evenly as possible, with heavier days first so the Medium/Hard-heavy final stretch is lighter.
- `--start DATE` - `YYYY-MM-DD`, `today`, or `monday`; skips the interactive prompt.
- `--seed N` - reproducible spaced plan.
- `--order roadmap|spaced` - `roadmap` walks NeetCode topics top-to-bottom; `spaced` (default) cycles categories.
- `--completed ...` - problem names to pre-check.
- `--output FILE` - write/overwrite a specific markdown file.

Difficulty phases scale with the plan length (e.g. for 90 days: Early = days 1-22, Middle = 23-58, Late = 59-90).


## 📁 Files

- **`generate_study_plan.py`** - Main generator script
- **`neetcode_250_complete.json`** - Master dataset with all 250 problems
- **`NeetCode_250_Study_Plan.md`** - Generated study plan
- **`CLAUDE.md`** - Technical documentation

## 🧠 Algorithm Features

### Intelligent Category Distribution
- Categories weighted by difficulty and day progression
- Spaced repetition with 6-day penalty for recently used categories
- Preference for categories with 2+ available problems

### Difficulty Progression
- **Days 1-30**: Mostly Easy problems with some Medium
- **Days 31-80**: Mixed Easy/Medium with some Hard
- **Days 81-125**: Emphasis on Medium/Hard problems

### Quality Assurance
- Verification that all 250 problems are included
- Statistics on category focus and difficulty distribution
- Analysis of plan effectiveness across different phases

## 📊 Example Output

```markdown
## Day 1 - 2025-07-07
**Topic:** Backtracking

**Problems:**
- [ ] 🟢 [Sum of All Subsets XOR Total](https://leetcode.com/problems/sum-of-all-subset-xor-totals) - *Backtracking*
- [ ] 🟡 [Subsets](https://leetcode.com/problems/subsets/) - *Backtracking*
```

## 🎯 Study Strategy

1. **Focus on Categories**: Both daily problems are from the same category to build pattern recognition
2. **Progressive Learning**: Start with fundamentals, advance to complex algorithms
3. **Spaced Review**: Categories return at optimal intervals for memory retention
4. **Consistent Practice**: 2 problems daily maintains steady progress without burnout

## 📈 Success Tips

- Complete problems in order for optimal learning progression
- Focus on understanding patterns within each category
- Use checkboxes to track your progress
- Review previous category problems if you're struggling with new ones
- Aim for consistency rather than speed

## 🔧 Technical Details

- Uses `random.seed(42)` for reproducible plan generation
- Python 3.6+ required
- No external dependencies beyond standard library
- Generates markdown with checkbox format for easy tracking

## 🤝 Contributing

Feel free to:
- Report issues with problem categorization
- Suggest improvements to the scheduling algorithm
- Add new features or optimizations
- Share your success stories!

## 📜 License

This project is open source and available under the MIT License.

---

**Ready to ace your coding interviews?** Generate your personalized study plan and start your 125-day journey to mastery! 🚀