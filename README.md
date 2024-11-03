# Student Request Manager

## Team members:

* Barbu Alexandru Daniel
* Oprea Horatiu

## The idea:

This is a web app designed to help students get answers faster from the university. The app will:

- Show Frequently Asked Questions;
- Send requests templates to be filled out;
- Send and receive official documents at a click of a button;

## Contributing:

1. Fork this repo.

2. On the GitHub web interface click `Sync fork` (button is right under the `code` button).

3. Clone the repo you just forked on your machine.

4. Add a remote connection to the original repository with `git remote add upstream <the URL of the original repo>`.

5. Make a branch with your name using `git checkout -b ＜new-branch-name＞`.

6. Add all the files that are modified using `git add <path-to-file>`.

>_**NOTE!!**_ If you accidentally added files, but not on a separate branch use `git reset` command, create the branch then use `git add <path-to-file>`.

7. You need to sync the local repo on your machine with the original repo, then commit so that no new files are lost. You will use `git fetch upstream`.

8. Commit changes to your repo: `git commit -sm "Write some message here"`.

9. Once you are finished run `git push origin <your-branch>`.

10. Create a Pull Request (PR) from the web side of github.

11. Merge the upstream changes into your branch.
```bash
git checkout <your-branch>
git merge upstream/main
```

12. You may have some new changes in your project now, push them on your fork.
```bash
git push origin <your-branch>
```