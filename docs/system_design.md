# System design

## Generic backend

The backend for this application is agnostic to actual platform where the end-user interacts with it. So while the plan is to use it at first for a Telegram bot, it should be easy to just adopt in other frontends too.

**Infrastructure:**

- Python backend - The backend logic is written in python
- Postgres storage - Taps are stored in Postgres
- Redis - Taps are scheduled to notify users, these events are stored in Redis

### Workflow details

**New tap creation:**

1. Insertion entry point is called in the backend
2. The user is authenticated - if it's from a verified bot user, not auth is needed
3. The request is then inserted into the Postgres SQL db
    - The tap will have a certail notification time
    - The tap will have a validity of 0
    - The tap is indexed in the table by an ID-Notification time
4. The request is also pushed through celery and scheduled for later
5. A backend component using celery listens for events continuously
6. The listener is triggered by a notification that is expiring
    1. The listener gets the notification, it gets its ID and then it requests Postgres SQL for the entry
    2. If the validity version in Postgres and Redis are the same, a notification is sent to user about the tap
        - If they are different, no-op

**Tap editing:**

This describes the scenario where the user edits the Tap, one example is by
changing the time at which it triggers.

1. Edit entry point is called
2. Auth...
3. The request is handled at the DB level
    - The tap changes its time and then its validity increase by 1
4. The updated TAP is pushed for scheduling with celery
5. Once the time for the old tap to be triggered comes
    - A call to DB is made and it is seen that the entry in Redis has a different validity version compared to Postgres - NO OP
6. The Tap is still triggered but under the new notification time
