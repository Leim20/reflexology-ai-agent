# 📢 Scheduled Broadcast System - User Guide

Complete guide for using the scheduled broadcast/promotion push message system.

---

## 📋 **What is This?**

The Broadcast System allows staff to **schedule promotional messages** that are automatically sent to customers at a specified date and time via WhatsApp.

**Use Cases:**
- 🎉 New Year promotions
- 🎊 Special event announcements
- 💝 Birthday greetings
- 🏷️ Weekend discounts
- 📣 New service launches
- 🎁 Member-only offers

---

## 🚀 **Quick Start**

### **Step 1: Setup (One-Time)**

Run the setup script:

```bash
# On VPS
cd /root/reflexology-agent
python3 scripts/setup_broadcast_sheets.py
```

This creates 3 new sheets in your Google Spreadsheet:
1. **Broadcast Recipients** - Customer list
2. **Scheduled Broadcasts** - Promotional messages
3. **Broadcast Logs** - Delivery tracking

---

### **Step 2: Add Recipients**

Open your Google Sheet:
https://docs.google.com/spreadsheets/d/YOUR_GOOGLE_SHEET_ID

Go to **"Broadcast Recipients"** sheet.

**Add customers:**

| Name          | Phone         | Status  | Added Date  | Notes       |
|---------------|---------------|---------|-------------|-------------|
| John Lee      | 60123456789   | Active  | 2025-11-26  | VIP Member  |
| Mary Tan      | 60198765432   | Active  | 2025-11-26  | Regular     |
| Ahmad Ali     | 60187654321   | Active  | 2025-11-26  |             |

**Column Guide:**
- **Name**: Customer name (for tracking)
- **Phone**: WhatsApp number (format: 60123456789)
- **Status**: Must be `Active` to receive broadcasts
- **Added Date**: When added (auto-filled by system if using add_recipient function)
- **Notes**: Optional notes (VIP, Member, etc.)

---

### **Step 3: Schedule a Broadcast**

Go to **"Scheduled Broadcasts"** sheet.

**Add a promotion:**

| Broadcast ID | Title                | Message                                      | Schedule Date | Schedule Time | Target List     | Status  | Sent Count | Created Date | Sent Date |
|-------------|----------------------|----------------------------------------------|---------------|---------------|-----------------|---------|------------|--------------|-----------|
| BC001       | CNY 2026 Promotion   | 🎊新年优惠！全场8折！Limited time only!      | 2026-01-15    | 10:00         | All Recipients  | Pending | 0          | 2025-11-26   |           |
| BC002       | Weekend Special      | This weekend only: RM99 for 90min massage!  | 2025-11-30    | 09:00         | All Recipients  | Pending | 0          | 2025-11-26   |           |

**Column Guide:**
- **Broadcast ID**: Unique ID (e.g., BC001, BC002, BC003...)
- **Title**: Internal reference name
- **Message**: The actual message to send (can be English/Chinese)
- **Schedule Date**: When to send (format: YYYY-MM-DD)
- **Schedule Time**: Time to send (format: HH:MM)
- **Target List**: Currently `All Recipients` only
- **Status**: Must be `Pending` to send
- **Sent Count**: Auto-filled after sending
- **Created Date**: When you added this broadcast
- **Sent Date**: Auto-filled when sent

---

### **Step 4: System Auto-Sends!**

The system checks **every 1 minute** for broadcasts ready to send.

When `Schedule Date + Schedule Time` is reached:
1. ✅ System sends WhatsApp message to all active recipients
2. ✅ Updates status to `Sent`
3. ✅ Records sent count
4. ✅ Logs each delivery in "Broadcast Logs" sheet

---

## 📊 **Tracking Deliveries**

### **View Broadcast Logs**

Go to **"Broadcast Logs"** sheet to see delivery details:

| Broadcast ID | Title           | Phone       | Name     | Sent Time           | Delivery Status | Response Received | Response Time | Response Text |
|-------------|-----------------|-------------|----------|---------------------|-----------------|-------------------|---------------|---------------|
| BC002       | Weekend Special | 60123456789 | John Lee | 2025-11-30 09:00:15 | Delivered       | Yes               | 2025-11-30 09:05 | Interested! When can I book? |
| BC002       | Weekend Special | 60198765432 | Mary Tan | 2025-11-30 09:00:18 | Delivered       | No                |               |               |
| BC002       | Weekend Special | 60187654321 | Ahmad    | 2025-11-30 09:00:21 | Failed          | No                |               |               |

**Column Guide:**
- **Broadcast ID**: Which broadcast this was
- **Phone/Name**: Who received it
- **Sent Time**: When delivered
- **Delivery Status**: Delivered / Failed / Error
- **Response Received**: Did they reply? (Yes/No)
- **Response Time/Text**: Their reply (auto-tracked when they respond)

---

## 🎯 **Best Practices**

### **1. Message Content**

✅ **Good Messages:**
- Clear and concise
- Include call-to-action
- Bilingual (English + Chinese) if needed
- Add urgency ("Limited time!", "Weekend only!")

```
🎊 Weekend Special 🎊

This weekend only:
RM99 for 90min foot massage!

Book now: 60120000000
```

❌ **Avoid:**
- Too long (keep under 200 characters)
- Too many emojis
- Unclear offers
- Spam-like content

---

### **2. Timing**

**Best Times to Send:**
- **Promotions**: 9:00 AM - 11:00 AM (when people check phones)
- **Event Reminders**: 8:00 AM (morning)
- **Weekend Specials**: Friday 9:00 AM
- **Birthday Greetings**: 8:00 AM on birthday

**Avoid:**
- Late night (after 10 PM)
- Too early (before 8 AM)
- During lunch (12-1 PM)

---

### **3. Frequency**

**Recommended:**
- Max 1-2 broadcasts per week
- Space them out (don't send daily)
- Only send valuable content

**Why?**
- Avoid spam complaints
- Maintain customer trust
- Higher engagement rates

---

## 🛠️ **Advanced Features**

### **Editing Before Send**

If you need to change a broadcast **before** it sends:
1. Find the row in "Scheduled Broadcasts"
2. Edit the message/date/time
3. Keep Status as `Pending`
4. System will send with new details

### **Canceling a Broadcast**

To cancel a scheduled broadcast:
1. Find the row in "Scheduled Broadcasts"
2. Change Status from `Pending` to `Cancelled`
3. System will skip it

### **Resending a Broadcast**

To resend an old broadcast:
1. Copy the broadcast row
2. Change Broadcast ID (e.g., BC002 → BC003)
3. Update Schedule Date/Time to future
4. Change Status to `Pending`
5. Clear Sent Count and Sent Date

---

## 📱 **Example Broadcasts**

### **1. New Year Promotion**

```
🎊 恭喜发财！CNY Promotion 🎊

Special CNY prices:
90min Body Massage: RM169 (Member: RM139)
120min with Cupping: RM199 (Member: RM169)

Valid: Jan 15-31, 2026
Book: 60120000000
```

**Schedule:**
- Date: 2026-01-15
- Time: 09:00

---

### **2. Weekend Flash Sale**

```
⚡ THIS WEEKEND ONLY! ⚡

Foot Massage 90min: RM99!
(Normal: RM139)

Book now: 60120000000
Limited slots available!
```

**Schedule:**
- Date: Friday before weekend
- Time: 10:00

---

### **3. Birthday Greeting**

```
🎂 Happy Birthday [Name]! 🎂

Enjoy your FREE 60min massage!
(Members only birthday benefit)

Book your slot today: 60120000000
Valid for this month only 😊
```

**Schedule:**
- Date: Customer's birthday month, 1st day
- Time: 08:00

---

## 🔧 **Troubleshooting**

### **Broadcast Not Sending**

**Check:**
1. Is Status = `Pending`? (Not "Sent" or "Cancelled")
2. Is Schedule Date/Time in the future or past?
3. Are there active recipients? (Status = "Active")
4. Is the application running? (Check `systemctl status chatbot`)

**Solution:**
```bash
# Check app logs
tail -f logs/ChatAgent_*.log | grep BROADCAST

# Check scheduler
tail -f logs/ChatAgent_*.log | grep SCHEDULER
```

---

### **Some Recipients Not Receiving**

**Check:**
1. Is their Status = `Active` in "Broadcast Recipients"?
2. Is phone number correct format? (60123456789)
3. Check "Broadcast Logs" for delivery errors

**Solution:**
- Update phone number format
- Set Status to `Active`
- Remove invalid phone numbers

---

### **Delivery Failed**

**Possible Reasons:**
1. Invalid phone number
2. Number not on WhatsApp
3. Blocked by recipient
4. Whapi API error

**Solution:**
Check "Broadcast Logs" sheet, look at "Delivery Status":
- `Failed` = Phone number issue
- `Error` = System error (check logs)

---

## 📊 **System Requirements**

- ✅ Google Sheets access
- ✅ Whapi WhatsApp API active
- ✅ Application running on VPS
- ✅ Scheduler enabled (runs every 1 minute)

---

## 💡 **Pro Tips**

1. **Test First**: Send to yourself first to preview
2. **Check Recipients**: Verify all phone numbers before big broadcast
3. **Monitor Logs**: Watch "Broadcast Logs" after sending
4. **Track Responses**: Note which promotions get best response rate
5. **Time Zones**: System uses Malaysia time (GMT+8)
6. **Personalization**: Use customer names in messages when possible

---

## 🎉 **Success Metrics**

Track these in "Broadcast Logs":

**Delivery Rate:**
```
(Delivered / Total Recipients) × 100
```

**Response Rate:**
```
(Responses / Delivered) × 100
```

**Conversion Rate:**
```
(Bookings from broadcast / Delivered) × 100
```

---

## 📞 **Support**

**Having issues?**

1. Check application logs:
   ```bash
   tail -f logs/ChatAgent_*.log | grep -i broadcast
   ```

2. Check broadcast stats:
   ```bash
   python3 scripts/setup_broadcast_sheets.py
   ```

3. Review "Broadcast Logs" sheet for errors

---

**Happy Broadcasting! 📣**
