# Tappy

## Project Description and Goals

There are several time management, task management and calendar management apps around app stores. They all come with shiny functionalities, some common some unique. But all missing some or other functionality that can be extremely useful for task management.

As such, with this project I intend to create a product that takes some of the insights I gained while working as a production engineer and apply them to day-to-day task management.

**Here is Tappy!**

Tappy presents as a task management framework centered around scheduling tasks, ack-ing that the time to work on them has started, and then marking them as completed once done.

Here are some examples of the workflows it allows:

Example single individual usage

**Studying for exam example:**
- User Ben creates a new **tap** for himeslf scheduled at 13:00 to study for his Intro to ML exam. Ben then goes about his day.
- At 13:00 Ben gets tapped about studying for his exam.
- Ben starts studying and then Acknowledges the tap for 1 hour
- Ben's ack expires after 1 hour and he is notified of it
- Ben marks the tap as completed

**Recurrent taps example:**
- User Ben wants to go to the Gym every day at 10am
- User Ben creates a recurrent **tap** for every day at 10am
- Every day Ben gets the tap at 10am, Acknowledges it for 1h 30m and then goes to the GYM
- By the time the ack expires Ben is done with the gym, he gets a notification about the expiry and that he needs to take action.
- He marks the **tap** as completed

**Snooze taps:**
- Ben is sometimes in the middle of doing something very important so he cannot action the tap.
- Tapps are meant to be nagging you to make sure you do things. So every 5 minutes since the **tap** was triggered and not actioned, Ben gets a new notification about needing to handle it.
- Ben is slightly annoyed but he still does not have the time to actually work on the **tap** he received, so instead he snoozes it for 10 minutes.
  - This allows Ben to not have to action it, but also get a reminder after 10 minutes to handle the tap.
  - Snoozing can be only done for 5/10/15 minutes, while acks are for any amount of time.
  - This is to make sure that we don't snooze something for a long time and then forget about it.
  - Acking on the other hand marks the beginnign of handling the task.

**Grouping:**

- Ben is married to George and they handle house chores together. A lot of time they don't care who does what as long as someone gets it done.
- Ben adds George to his Tappy group.
- Ben can now schedule taps for George or for the group
- Ben wants to make sure that someone takes the trash out, so he creates a Tap for the group at 18:00 "take out the trash"
- At 18:00 both Ben and George get the tap together, George is the first to see it and acks it for 5 minutes as he will take the trash out. Ben sees that George acked it so no action for him.
- 5 minutes later a new notification pops that the tap came unacked for both of them, George marks it complete. Both Ben and George see this.


# TODO:

- Create new Exception class for exceptions that need to be propagated to the user
- Create new decorator for telegram functions that need to handle exceptions and propagate them to the user
- Finish documentation for existing code
- Write notification dispatcher that works with celery and redis
- Write celery tasks for sending notifications
- Implement first simple tap logic to tap yourself and ack/complete it
