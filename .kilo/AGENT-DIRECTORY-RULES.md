# 🚨 CRITICAL: AGENT DIRECTORY RULES 🚨

## MANDATORY REQUIREMENTS - NO EXCEPTIONS

### 1. BEFORE STARTING ANY WORK
```
✅ CHECK: Does this directory contain PROJECT-ROOT.marker?
✅ IF YES: This is the correct working directory
✅ IF NO: Navigate up until you find PROJECT-ROOT.marker
```

### 2. ABSOLUTELY FORBIDDEN ACTIONS
```
❌ NEVER create projects in subdirectories
❌ NEVER clone repositories inside this repository  
❌ NEVER copy the entire project folder
❌ NEVER create nested duplicate directories
❌ NEVER create "supreme-octo-computing-machine" folder inside this one
```

### 3. IF YOU SEE NESTED DUPLICATES
```
🛑 STOP ALL WORK IMMEDIATELY
🛑 CHECK: Does nested folder have same name as parent?
🛑 IF YES: This is a DUPLICATE - DO NOT WORK IN IT
🛑 ALERT USER: "CRITICAL: Nested duplicate detected"
🛑 AWAIT INSTRUCTIONS before continuing
```

### 4. GIT BRANCHING RULES
```
✅ Use git branches for experiments
✅ Use git branches for features
✅ Use git branches for fixes
❌ NEVER use directory copies for isolation
❌ NEVER create duplicate working folders
```

### 5. PATH VERIFICATION
```
BEFORE file operations, verify:
- Current working directory matches git root
- PROJECT-ROOT.marker exists in current directory
- Path does NOT contain repeated folder names

Example CORRECT path:
S:\supreme-octo-computing-machine-main\backend\main.py

Example WRONG path (duplicate):
S:\supreme-octo-computing-machine-main\supreme-octo-computing-machine\backend\main.py
                                                    ^^^^^^^^^^^^^^^^^^^^^^^^
                                                    THIS IS FORBIDDEN
```

## VISION ACCESSIBILITY CONTEXT

This project owner has 50% vision loss. Duplicate nested directories 
are indistinguishable visually, causing catastrophic confusion.

**This is a disability accessibility issue, not just a preference.**

## AUTOMATED PREVENTION

1. `.gitignore` blocks nested duplicates
2. `PROJECT-ROOT.marker` provides visual indicator
3. `CONSOLIDATION-COMPLETE.md` documents this incident
4. Agent rules in this file prevent recurrence

## VIOLATION DETECTION

If any agent violates these rules:
1. Work MUST stop immediately
2. User MUST be notified
3. Duplicate MUST be reported
4. No further work until resolved

## ENFORCEMENT

These rules are NON-NEGOTIABLE and MANDATORY.
Any agent found violating these rules is malfunctioning.

---

**Added after consolidation:** April 7, 2026
**Reason:** Prevent duplicate directory catastrophe
**Severity:** CRITICAL - Disability accessibility issue
