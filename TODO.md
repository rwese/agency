# TODO: Rewrite Wizard with questionary

## Overview

Replace the broken Click-based wizard with `questionary` library for interactive prompts.

## Tasks

- [x] 1.1: Add questionary to dependencies
- [x] 1.2: Rewrite `_prompt_text` using questionary.text
- [x] 1.3: Rewrite `_select_option` using questionary.select
- [x] 1.4: Rewrite checkbox using questionary.checkbox
- [x] 1.5: Rewrite `_confirm` using questionary.confirm
- [x] 1.6: Remove manual `_getch` and termios usage
- [x] 1.7: Simplify `run_wizard` flow
- [ ] 1.8: Test wizard end-to-end (interactive)

## Done

- [x] Research: questionary selected as replacement library
