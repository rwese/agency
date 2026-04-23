# Demo Project 07: Password Strength Checker

**Type:** Library + CLI
**Complexity:** Medium
**Purpose:** Test pattern matching, entropy calculation, scoring

## Overview

A library and CLI tool for evaluating password strength based on multiple criteria.

## Features

- [ ] Length check (minimum 8, recommended 12+)
- [ ] Character class detection (lowercase, uppercase, digits, special)
- [ ] Common password detection (top 10k list)
- [ ] Pattern detection (keyboard walks, repeated chars, sequences)
- [ ] Entropy calculation
- [ ] Strength score (0-100)
- [ ] Crack time estimation
- [ ] Improvement suggestions
- [ ] Batch checking from file

## Tech Stack

- **Language:** Python
- **Dependencies:** None (pure implementation)

## CLI Interface

```bash
# Check single password
password-check "MyStr0ng!Pass"

# Get detailed analysis
password-check "MyStr0ng!Pass" --verbose

# Check from file
password-check --file passwords.txt

# Output formats
password-check "pass" --format json
password-check "pass" --format csv
```

## Output Example

```
Password: **************
Score: 85/100 (Strong)

Checks:
✓ Length >= 12 characters
✓ Contains uppercase letters
✓ Contains lowercase letters
✓ Contains digits
✓ Contains special characters
✓ No common password match
✓ No keyboard walk patterns
✓ No repeated characters

Entropy: 72.5 bits
Estimated crack time: 1,234 years

Suggestions:
- Consider using a passphrase
```

## Test Cases

| ID | Test | Description |
|----|------|-------------|
| TC01 | Weak password | "password123" scored low |
| TC02 | Strong password | Random 16+ char scored high |
| TC03 | Common password | "123456" detected |
| TC04 | Keyboard walk | "qwerty" detected |
| TC05 | Repeated chars | "aaaaaa" detected |
| TC06 | Sequence | "abcdef" detected |
| TC07 | Entropy calc | Entropy matches expected |
| TC08 | Crack time | Times are reasonable |
| TC09 | Suggestions | Suggestions are relevant |

## Task Breakdown

1. Create character class detector
2. Implement length checker
3. Add common password list (top 10k)
4. Implement pattern detectors (keyboard, repeated, sequence)
5. Calculate entropy
6. Estimate crack time
7. Generate improvement suggestions
8. Build CLI interface
9. Write unit tests for each check
10. Write integration tests
11. Create e2e test report

## Success Criteria

- Correctly scores known passwords (weak: <40, strong: >80)
- Detects common passwords from list
- Pattern detection catches keyboard walks
- Entropy calculation is accurate
- Crack time estimates are realistic
- Suggestions are actionable and relevant
