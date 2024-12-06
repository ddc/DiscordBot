# Single-database configuration


# Create version file
#### This will create a file with sufix `file_name`
```bash
alembic -c './config/alembic.ini' revision --autogenerate -m file_name
alembic -c './config/alembic.ini' upgrade head
```


# Apply all migration files to the database
```bash
alembic -c './config/alembic.ini' upgrade head
```


# Downgrade one revision
#### Revert the last file migration applied to the datatabse, file still going to be present
```bash
alembic -c './config/alembic.ini' downgrade head-1
```
