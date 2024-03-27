.PHONY: serve

serve:
	bundle exec jekyll serve

clean:
	rm -rf _site
	rm -rf .jekyll-cache
