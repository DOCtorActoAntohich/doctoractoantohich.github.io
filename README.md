# W e b s i t e

Personal notes and stuff.
Got nothing better to do basically.

## How to run locally

I will forget it. I already forgor it once.
It's for myself anyway.

Install Ruby if needed:

```bash
brew install chruby ruby-install xz
```

Download ruby version from [`.ruby-version`](./.ruby-version) and activate it.
Then install dependencies.

```bash
ruby-install ruby 3.1.3
chruby ruby-3.1.3
gem install github-pages
```

Then run `make serve` to just run locally.

To see it from other devices in local network, go for the following command.
If you bind to `0.0.0.0` it will redirect you to a wrong location,
so use your machine's IP address here.

```bash
bundle exec jekyll serve --host <YOUR-LAN-IP>
```
