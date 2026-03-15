# SPENDING EMERGENCY

**You were charged $250 unexpectedly. This file tells you exactly what to do right now.**

---

## What Happened (Plain English)

### The confusion: two completely separate Anthropic accounts

Anthropic runs two billing systems that share the same company name but share **no money**:

| What you think you're paying | What it actually is | Does Kilo use it? |
|------------------------------|--------------------|--------------------|
| Claude.ai Pro — $30/month subscription | Access to the **claude.ai website** only | ❌ No |
| Anthropic API — pay per token | Direct developer access, billed per message | ✅ Yes — this is what charged you |

### What you did (and why it seemed right at the time)

1. Kilo stopped working.
2. You tried to fix it by connecting Kilo to your Claude account.
3. Kilo asked for an **API key** — so you created one at console.anthropic.com.
4. That key looked like it was from Anthropic (same company, same login), so it seemed like it should use your $30/mo plan.
5. **It does not.** The moment you created that key, you opened a second, separate pay-per-use billing account.
6. Every message sent through Kilo from that point billed this second account at per-token rates — completely separate from your $30/mo subscription.

### Why the $30/month plan could not help

The Claude.ai Pro subscription is locked to the claude.ai website. There is no way to connect Kilo Code (or any third-party app) to your Claude.ai subscription. Anthropic does not offer that feature. If you want to use Claude in Kilo, you **must** use an API key, and API keys are always pay-per-use.

This is Anthropic's design, not something you did wrong. It is a common trap for new users.

---

### The $250 came from the API key account, not the subscription.

---

## Step 1 — Stop All Further Charges RIGHT NOW

**Do this before anything else. Takes 2 minutes.**

1. Open a browser and go to: **https://console.anthropic.com**
2. Sign in with the same email you use for Kilo/Claude.
3. Click **"API Keys"** in the left sidebar.
4. Find the key that Kilo was using. It will be listed there.
5. Click the **trash icon** or **"Revoke"** to permanently disable it.
6. Confirm the deletion.

The key is now dead. No more charges can come from it.

---

## Step 2 — Set a Hard Spending Limit (Do This Next)

1. Still in **https://console.anthropic.com**
2. Click **"Settings"** or **"Billing"** in the left sidebar.
3. Find **"Usage Limits"** or **"Spending Limits"**.
4. Set the **Monthly Spending Limit** to an amount you are comfortable with — for example: **$10**.
5. Save it.

This means even if a key is accidentally left active in the future, it can never charge more than your limit per month.

---

## Step 3 — Run the Emergency Stop Script on Your PC

Run this in a PowerShell terminal inside VS Code to blank the key from Kilo's settings:

```powershell
./scripts/emergency-stop-api.ps1
```

This removes the API key from Kilo's VS Code configuration files so it cannot make any more calls, even if you accidentally open VS Code.

---

## Step 4 — Request a Refund From Anthropic

Anthropic does consider refund requests, especially for unexpected charges.

**Email to send:**

- Address: **support@anthropic.com**
- Subject line: `Unexpected $250 API charge - account holder on disability assistance`

**What to include:**
- Your account email
- The date you noticed the charge
- That you have a Claude.ai $30/mo subscription and believed Kilo was using that
- That you did not knowingly configure a pay-per-use API key or understand the difference
- That you are on disability assistance and cannot absorb this charge
- That you have now revoked the key and set a spending limit

There is no guarantee of a refund, but Anthropic support has helped people in similar situations, especially on a first incident.

---

## Step 5 — How to Use Kilo for Free (or Very Cheaply) Going Forward

**Option A: Use your Claude.ai subscription in Kilo** *(no extra cost)*

Kilo Code supports logging in with your Claude.ai account instead of an API key.

1. Open VS Code → Kilo panel → Settings (gear icon).
2. Under **API Provider**, look for **"Use Claude.ai account"** or **"Log in with Anthropic"**.
3. Sign in with your Claude.ai credentials.
4. Delete or leave blank the **API Key** field.

When set this way, Kilo uses your $30/mo subscription allowance, not pay-per-use.

**Option B: Use a free local model (zero cost forever)**

Install Ollama (free) on your PC and point Kilo at it:

1. Download Ollama from https://ollama.com (free, Windows installer).
2. Run: `ollama pull llama3.2` in a terminal (downloads a free model).
3. In Kilo settings → API Provider → choose **Ollama**.
4. Set base URL to `http://localhost:11434`.
5. Pick a model. Zero cloud cost. No API key needed.

**Option C: Set a $5/month API key spending limit**

If you prefer to keep using an API key, set the spending limit to $5/mo in the Anthropic console. The key stops working the moment you hit $5, so you can never be surprised again.

---

## Why Kilo Appeared Broken But Was Still Charging

When Kilo crashes or shows an error *on screen*, the extension can still send API requests in the background before showing the error. You see a broken UI, but Anthropic's servers already received and processed the request and billed for it.

This is why the extension "not working" does not mean "not charging."

---

## Quick Summary Checklist

- [ ] Go to console.anthropic.com and **revoke the API key** (Step 1)
- [ ] Set a **monthly spending limit** in Anthropic billing (Step 2)
- [ ] Run `./scripts/emergency-stop-api.ps1` on your PC (Step 3)
- [ ] Email support@anthropic.com to **request a refund** (Step 4)
- [ ] Switch Kilo to use your Claude.ai account login instead of an API key (Step 5)
