---
title: Multiple Git Accounts
description: Settings up commit email per directory
layout: standard
created_at: 2024-04-10
---

You can change your commit name and email on per directory basis.

## What we have

Assume you have all repositories in `~/repos/` folder.

You have your `personal` and `work` folders
where you need to use different names and commit emails.

### Creating separate configs

Now in `~/repos/personal/` create `.gitconfig-personal` file with these contents:

```toml
[user]
    name = My epic nickname
    email = example@gmai.com
```

Also, in `~/repos/work/` create `.gitconfig-work` file:

```toml
[user]
    name = My full name for work
    email = red@a-mog.us
```

### Including configs in global `.gitconfig`

Add the following lines to your `~/.gitconfig`.

```toml
[includeIf "gitdir:~/repos/personal/"]
    path = ~/repos/personal/.gitconfig-personal
[includeIf "gitdir:~/repos/work/"]
    path = ~/repos/work/.gitconfig-work
```

Note that you should not have other `[user]` settings
in global `.gitconfig` for it to work properly.

## The result

- Whenever you create a new `personal` Git repo
  your user settings will be loaded from `.gitconfig-personal`.
- For your `work` repositories,
  it'll load user settings from `.gitconfig-work`

You can always double-check it by running
`git config --list` in any repository.
