---
title: Testable Dramatiq and Dependency Injection
description: >
    Making dramatiq actors testable by avoiding
    global variables and specifying dependencies explicitly.
layout: standard
created_at: 2024-03-11
---

When I write my stupid code, I follow some basic rules, and one of them is as follows:

> Design your system to be testable.

After working with FastAPI a lot, I got too used to its great dependency injection system.

```python
@app.get("/users")
async def get_list_of_all_users(
    users_repository: UsersRepository = Depends(get_users_repository)
) -> list[User]:
    return await users_repository.get_all()
```

This is just a random example (as everything here lol), but I hope you get the idea.

The `UsersRepository` is a clear and explicit dependency for this function.
You can easily write auto-tests for this endpoint, and
if you really need it - mock the `UsersRepository`.

Yeah, you can say "You don't have to test everything" and be asbolutely right,
but it's not an excuse to write shitty code.
Soooo I think writing testable code already solves many problems,
and then when you need it the most, just go write those damn tests.
All that BS is just a skill you can develop over time.

## Why Dramatiq gives me a headache

Dramatiq, however, does not have any dependency injection.
Or maybe I suck at googling? Who knows.

Presenting to you _The case_.

Imagine we have some classes like:

- `Message` - something that belongs to our business domain. Non-JSON-encodable dataclass.
- `MessageDict` - same as `Message` but is JSON-encodable and has no behavior.
  To make it JSON-encodable, we have to make it a `TypedDict` subclass with
  all `dict` items being JSON-encodable.
- `EpicDecisionMachine` - some class that (epically) makes decisions :nerd:.
  Non-JSON-encodable either.

The example is rather abstract. Don't focus on implementation - it's bullshit.

```python
@dramatiq.actor
async def process_message(message: MessageDict) -> None:
    real_message = Message.from_dict(message)
    if real_message is None:
        raise RuntimeError("Couldn't parse message")

    # This is a dependency that may have its own dependencies.
    decision_machine = EpicDecisionMachine(...)

    decision = await decision_machine.process(real_message)
    if decision.is_epic():
        apply_decision.send(decision.as_dict())


@dramatic.actor
async def apply_decision(decision: DecisionDict) -> None:
    ...
```

I see multiple problems with this code, and it goes against my silly rules.

1. I can only supply JSON-encodable arguments to actors.
2. There are implicit dependencies, such as `EpicDecisionMachine` class and `apply_decision` actor.
3. I don't know how to test this code.

Okay, I can accept the first point - it's just a feature/limitation of Dramatiq.
No problem, I don't mind supplying the primitive types only.
But there's no way I can swallow it and accept the other problems.

I could extract some implicit dependencies as global variables, but is it any better?
In my absolutely 100% correct and unbiased expert professional super-duper opinion, it isn't better.
Even though you can monkey-patch them, they're still implicit dependencies.

```python
decision_machine = EpicDecisionMachine(...)

@dramatiq.actor
async def process_message(message: MessageDict) -> None:
    # Oversimplified, but you get the idea:
    # It's created somewhere outside of the actor now.
    decision_machine.dance(...)
```

This approach still doesn't make it easier for me to write tests.
Yeah I read [their documentation](https://dramatiq.io/guide.html#unit-testing) and
surprisingly unit tests worked.
They weren't a blast to write though - I still was not so sure
if the actual business logic worked as expected.

So I decided to cure my headache by doing some crazy
schizophrenia-fueled shit that I'll explain to you now.

We'll solve those problems by combining these two principles:

- Separating the business logic from external services.
- Using closures to avoid global variables.

## Extracting the business logic

The actual business logic was hidden somewhere in the actor.
You can test the actor but it's notably harder and requires more effort.

Soooooo I extracted the business logic into a separate object.

```python
class OnEpicDecisionFoundCallback(typing.Protocol):
    def __call__(self, decision: Decision) -> None: ...

class MessageBrain:
    def __init__(
        self,
        decision_machine: EpicDecisionMachine,
        on_epic_decision_found: OnEpicDecisionFoundCallback,
    ) -> None:
        self.decision_machine = decision_machine
        self.on_epic_decision_found = on_epic_decision_found
    
    async def raw_perform(self, message: MessageDict) -> None:
        real_message = Message.from_dict(message)
        if real_message is None:
            raise RuntimeError("I become die")
    
        await self.perform(real_message)
    
    async def perform(self, message: Message) -> None:
        decision = await self.decision_machine.process(real_message)
        if decision.is_epic():
            self.on_epic_decision_found(decision)
```

The benefits are as follows:

- Clear dependencies - this business logic becomes easily testable.
- Decoupling - independent actors don't know about each other.
- Single Responsibility (sorta) - we separated business process from data conversion.

Okay, it's cool and all, but how do we now use it in actor?

## Using closures to avoid global variables

Sadly, we can't fully avoid global variables - it seems like
dramatiq wants to have `broker` as a global variable in file.
Well, I can accept that as long as there isn't any other trash in the global scope.

Let's do the thing, then. Take a look at `broker.py`, with imports omitted cos I'm lazy.

```python
# In 1.14 it works as follows.
broker = RedisBroker(host=redis_host())
broker.add_middleware(dramatiq.middleware.asyncio.AsyncIO())
dramatiq.set_broker(broker)

# Not 3.12 sorry.
MessageBrainActor: TypeAlias = dramatiq.Actor[[MessageDict], Awaitable[None]]
DecisionApplyingActor: TypeAlias = dramatiq.Actor[[DecisionDict], Awaitable[None]]

def make_message_brain_actor(message_brain: MessageBrain) -> MessageBrainActor:
    # The inner function captures the scope of outer function.
    # Basically, that's how you "inject" a dependency in it.
    async def process_message(message: MessageDict) -> None:
        await message_brain.raw_perform(message)
    
    # Dramatiq registers actor with this line.
    # You don't really have to store them anywhere.
    return dramatiq.actor(process_message, broker=broker)


# Same idea basically - it just injects something.
# I'll omit the details though.
def make_decision_applying_actor(...) -> DecisionApplyingActor:
    async def apply_decision(decision: DecisionDict) -> None:
        ...
    
    return dramatiq.actor(apply_decision, broker=broker)
```

Now we can create our actors somewhere in `dramatiq_main.py`

```python
from broker import make_message_brain_actor, make_decision_applying_actor

def dramatiq_main() -> None:
    decision_applying_actor = make_decision_applying_actor(...)

    def on_epic_decision_found_callback(decision: Decision) -> None:
        # encoding some message and sending it to another actor. 
        decision_applying_actor.send(decision.as_dict())
    
    decision_machine = EpicDecisionMachine(...)
    mesage_brain = MessageBrain(decision_machine, on_epic_decision_found_callback)
    mesage_brain_actor = make_message_brain_actor(message_brain)


dramatiq_main()
```

Now what happens when we start up Dramatiq workers by executing `dramatiq my_app.dramatiq_main`:

- It imports the `broker.py` and registers the broker.
- It does not yet create any actors.
- It enters the `dramatiq_main` function and finally creates actors with injected dependencies.
- Finally, workers start working hard as fuck and accepting messages.

After that, you can create the same actors in your main app,
or make any dummies if you only need to `send`.
I'd still recommend creating them in the same way
cos you may need to directly call them sometimes.

What has improved after this step:

- Actors now have clear dependencies.
- These dependencies are explicitly injected into them on initialization stage.
- All actors are now one-liners - you don't even need to test them anymore.
  Focus on testing your business logic instead.
- Actors are independent - you can replace the callback with anything you want.
- Business logic is separated from sending/receiving the data.

## Conclusion

Nothing much, I just like experimenting sometimes.

This page is the answer to my own questions I asked to my friend google
(he was really speechless and couldn't answer. dumbass).

Maybe this will help someone, idk.
