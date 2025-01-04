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

>_**NOTE!!**_ Use **WSL**, nothing else!! 🚀

1. Clone the repo.
    1. Make the virual enviroment using `python3 -m venv venv`.
    2. Run `source venv/bin/activate`.
    3. Then run `pip install -r requirements.txt`.
2. Make a branch with your name using `git checkout -b ＜new-branch-name＞`.
3. Write your code.
4. Add all the files that are modified using `git add <path-to-file>`.
5. Commit changes to your repo: `git commit -sm "Write some message here"`.
6. Once you are finished run `git push origin <your-branch>`.
7. You will let me merge the branch.

>_**NOTE!!**_ Only one must do the merging!!
>_**NOTE!!**_ If you accidentally added files, but not on a separate branch use `git reset` command, create the branch then use `git add <path-to-file>`.

8. Occasionally update your local project using `git fetch`.
>_**NOTE!!**_ Updating is not optional, is **MANDATORY**. 😑

9. Merge the upstream changes into your branch.
```bash
git checkout <your-branch>
git merge upstream/main
```

10. You may have some new changes in your project now, push them on your fork.
```bash
git push origin <your-branch>
```


## How to run the app:

Set up those enviromen variables:
```bash
export FLASK_APP=project
export FLASK_DEBUG=1
```
And then run
```bash
flask run
```