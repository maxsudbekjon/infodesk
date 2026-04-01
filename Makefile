merge-prod:
	git pull origin --no-rebase $(branch)
	git add .
	git commit -m "merge"
	git push origin prod

pull-prod:
	git pull origin prod


