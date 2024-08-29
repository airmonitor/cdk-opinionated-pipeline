# Commiting changes to the repository
1. Amend your changes
2. Invoke the pre-commit hooks:
   ```shell
   make pre-commit
   ```
3. Invoke the tests:
   ```shell
   make tests
   ```
4. If the tests pass, commit your changes. In contrary, if the tests fail, fix the issues by updating test artifacts - snapshots
    ```shell
   make udpate-tests
   ```
5. Commit your changes and push them to the remote repository.
