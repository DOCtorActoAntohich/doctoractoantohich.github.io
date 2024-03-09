# frozen_string_literal: true

Gem::Specification.new do |spec|
  spec.name          = "funny-theme"
  spec.version       = "0.1.0"
  spec.authors       = ["DOCtorActoAntohich"]
  spec.email         = ["fairy666death@mail.ru"]

  spec.summary       = "Custom theme that's not supposed to be used anywhere else"
  spec.homepage      = "https://github.com/DOCtorActoAntohich/doctoractoantohich.github.io"
  spec.license       = "MIT"

  spec.files         = `git ls-files -z`.split("\x0").select { |f| f.match(%r!^(assets|_layouts|_includes|_sass|LICENSE|README)!i) }

  spec.add_runtime_dependency "jekyll", "~> 3.9"

  spec.add_development_dependency "bundler", "~> 1.16"
  spec.add_development_dependency "rake", "~> 12.0"
end
