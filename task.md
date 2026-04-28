
# 1. Core Features You Described

Your app (phase 1):

### Client

* Browse venues (futsal, cricket, badminton)
* View available hourly slots
* Book slot
* Pay online
* Chat with owner
* Rate venue
* Booking history

### Owner

* Add venue
* Set pricing per hour
* Set available time slots
* Receive booking notifications
* Accept / auto-confirm booking
* Chat with client
* Dashboard (earnings, bookings)

### System

* Payment integration
* Notification system
* Ratings
* Owner ↔ Client chat only
* Hourly booking logic

---

# 2. High Level Architecture

```
React Web (Owner + Client)
React Native Mobile
        |
        |
     Django API (DRF)
        |
        |
PostgreSQL Database
        |
Redis (chat + notifications optional)
```

---

# 3. Database Schema (Recommended)

I'll design production-ready schema.

---

# User Table (Custom Django User)

You should use **custom user model**

```
User
----
id
name
email
phone
password
role (OWNER / CLIENT)
is_verified
created_at
```

---

# Venue Table

Owner can create multiple venues

```
Venue
-----
id
owner_id (FK → User)
name
description
location
latitude
longitude
sport_type (FUTSAL / CRICKET / BADMINTON)
price_per_hour
opening_time
closing_time
rating_avg
created_at
```

---

# Venue Images

```
VenueImage
----------
id
venue_id (FK)
image
```

---

# Time Slot Table (Important)

You can either:

* generate dynamically OR
* store in DB

I recommend storing in DB

```
TimeSlot
--------
id
venue_id (FK)
date
start_time
end_time
is_available
```

Example:

```
Venue 1
2026-04-28
6:00 - 7:00
7:00 - 8:00
```

---

# Booking Table

```
Booking
-------
id
venue_id (FK)
client_id (FK → User)
date
start_time
end_time
total_price
status (PENDING / CONFIRMED / CANCELLED)
payment_status (PENDING / PAID)
created_at
```

---

# Payment Table

```
Payment
-------
id
booking_id (FK)
amount
payment_method (ESEWA / KHALTI / STRIPE)
transaction_id
status (SUCCESS / FAILED)
paid_at
```

---

# Review / Rating Table

```
Review
------
id
venue_id (FK)
client_id (FK)
rating (1-5)
comment
created_at
```

---

# Chat System (Owner ↔ Client)

Simple 1-to-1 chat per booking

```
ChatRoom
--------
id
booking_id (FK)
client_id
owner_id
created_at
```

```
Message
-------
id
room_id (FK)
sender_id
message
is_read
created_at
```

This ensures:

* client can't chat other clients
* chat only after booking

---

# Notification Table

```
Notification
------------
id
user_id
title
message
type (BOOKING / PAYMENT / CHAT)
is_read
created_at
```

# 5. API Structure

### Auth

```
POST /api/register
POST /api/login
```

### Venue

```
GET /venues
GET /venues/{id}
POST /venues (owner)
PUT /venues/{id}
```

### Slot

```
GET /venues/{id}/slots?date=2026-04-28
```

### Booking

```
POST /booking
GET /my-bookings
```

### Chat

```
GET /chat/rooms
GET /chat/messages/{room_id}
POST /chat/send
```

### Review

```
POST /review
GET /venue/{id}/reviews
```
