NAME=***REMOVED***stats-man
VERSION=latest

.PHONY: build

run: build
	docker run -it --rm $(NAME):$(VERSION)

build:
	docker build --pull -t $(NAME):$(VERSION) .

clean:
	docker rmi $(NAME):$(VERSION)

push:
	docker push $(NAME):$(VERSION)