# Data Science Docker (DSD)

DSD is a docker manager for data science users on a host machine.
It provide each user an independent environment and allow users to share the computational resources on the host without disturbing other users.
The provided environment is simple but powerful, with which users can work on their data science project right away.
It also integrate management of NVidia GPU resources for easy and independent access.

## NOTICE

This project is under heavy develop.
Before any update, make sure your repository is up-to-date.

## Developer Guide

We use a fork & pull-request workflow.
Every developer fork this baseline repository and develop on his/her own repository.
After certain progress being made, submit a pull-request to the baseline repository.

Following are basic steps to work on the code.

1. Fork the baseline repository.

2. Clone your own repository to a local working directory.
```
git clone git@git.oschina.net:[your_own_name]/dsd.git
```
You may need this [instruction](https://git.oschina.net/oschina/git-osc/wikis/%E5%B8%AE%E5%8A%A9#ssh-keys) if this is your first clone on `git.osc`.

3. Pull from the baseline repository to your own repository to keep it up-to-date.
You may want to use the "sync" button on the web interface.

4. Change to your local project root. Pull from your own repository.
```
git pull
```

5. Resolve conflict if there is any, and commit, of course.

6. Start working with your code. You may want to use the container for `dsd-console`.

    1. Change to `dsd/docker/dsd`
    ```
    cd dsd/docker/dsd
    ```

    2. Follow `readme.md` there. Basically, just use the `run.sh` script. Should be required to provide `sudo` privilege.
    ```
    chmod u+x run.sh
    ./run.sh
    ```

    3. A container will be create and run with web interface exposed. Follow the promoted links.

    4. Go to the `jupyter` links first, using a browser.
    Then you will have a web access to the container and be able to develop in it. Project root `dsd` will be map to `~/workspae/dsd`. You can also use any `git` command there. `ssh-key` of the current user are also mapped. You will have the same privilege.

    5. To work on the web app, change to `dsd/python` and use `init_db.sh` to initialize the database. More information are available in `readme.md` there.

7. With any progress, commit your update. Push a group of commits to your own repository after that.
```
git commit
git push
```

8. Submit a pull-request on the web interface back to the baseline repository.

9. Watch the notifications from both email and the web interface. Read the comments and fix and issue presented, until the acceptance of the pull-request. You can commit and push any modification during this time and they will be append to the pull-request.

10. After the pull-request being accepted, you already know how we work, together. Go back to step 3 and it is another day now.

Life Would Be Easier If I Had The Source Code.
