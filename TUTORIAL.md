# PrivateDrive: Step-by-Step Tutorial 📂
**How to Access Your Live Data from Anywhere Without Transferring Files**

This tutorial explains how to run your own private server and mount it as a **live virtual drive (`Z:\`)** on any other computer or phone across the internet—for 100% free.

---

## 🌟 Why This Solves the "Tally / Accounting" Problem
* **Zero file transfers:** Files are never copied to Google Drive or downloaded onto second laptops.
* **Single source of truth:** All entries, bills, and edits save **directly onto the main computer's hard drive** in real time.
* **No conflicting files:** Multiple people won't end up with desynchronized copies.

---

## Part 1: How to Start the Server on the Main Computer

1. Open the `privatedrive` folder on your main computer.
2. Double-click **`run.bat`** (on Windows) or run `./run.sh` (on Linux).
3. A terminal window will open and display:
   * **Web Dashboard:** `https://xyz.app.lhr.life`
   * **Virtual Drive URL:** `https://xyz.app.lhr.life/drive`
   * **Username:** `admin`
   * **Password:** (e.g. `Pass5281`)
   * **A Ready-to-use Windows Command**

*(Leave this window open in the background while you want to access your data).*

---

## Part 2: How to Connect from Your Second Laptop (Anywhere in the World)

### Method A: The 1-Click Fast Way (Recommended)
1. On your second laptop, press the **Windows Key**, type **cmd**, and open **Command Prompt**.
2. Paste the command shown on your server screen:
   ```cmd
   net use Z: "https://xyz.app.lhr.life/drive" /user:admin YourPassword /persistent:yes
   ```
3. Press **Enter**.
4. You will see: **`The command completed successfully.`**
5. Open **File Explorer** → you will now see **`Drive Z:\`** listed under "This PC"!

---

### Method B: The Visual Way (Via File Explorer)
1. On the second laptop, open **File Explorer**.
2. Click **"This PC"** on the left sidebar.
3. In the top toolbar, click **•••** (or right-click "This PC") and select **"Map network drive..."**.
4. Set **Drive:** `Z:`
5. In **Folder**, paste your Drive URL: `https://xyz.app.lhr.life/drive`
6. Check the box: **"Connect using different credentials"**.
7. Click **Finish**.
8. A Windows Security popup will ask for your credentials:
   * **Username:** `admin`
   * **Password:** (your password)
9. Click **OK**. Drive `Z:\` will immediately open!

---

## Part 3: How to Use Tally & Other Software with Drive Z:

### In TallyPrime / Tally.ERP 9:
1. Open Tally on your second laptop.
2. Go to **Select Company** → press **F1** (or click **Specify Path**).
3. Type:
   ```text
   Z:\
   ```
   *(or `Z:\Data` if your data is in a subfolder)*.
4. Tally will immediately list your companies directly from the main machine!
5. Any invoice, voucher, or ledger you create will save directly to the main computer.

### In Excel, Word, or Billing Software:
1. When opening or saving a file, simply browse to **This PC → Z: Drive**.
2. Open the file, make changes, and hit `Ctrl + S`. It saves directly to the main computer.

---

## Part 4: How to Connect from an iPhone or Android Phone

* **On iPhone / iPad:**
  1. Open the built-in **Files** app.
  2. Tap the **•••** button at top right → tap **"Connect to Server"**.
  3. Enter: `https://xyz.app.lhr.life/drive`
  4. Select **Registered User** → enter `admin` and password.
  5. You can now browse, open, and save files straight to the main computer.

* **On Android:**
  1. Install **Cx File Explorer** (free from Google Play Store).
  2. Open the app → tap **Network** tab → tap **+ (New location)**.
  3. Select **Remote** → choose **WebDAV**.
  4. Enter your Drive URL, username, and password.

---

## Summary Checklist

| Action | Where to do it | What happens |
| :--- | :--- | :--- |
| **1. Start Server** | Main computer (run `run.bat`) | Creates secure private drive portal |
| **2. Map Drive** | Second laptop (run `net use Z: ...`) | Adds live `Z:\` drive in File Explorer |
| **3. Open Software** | Second laptop (Tally/Excel) | Directly uses data from main computer |
