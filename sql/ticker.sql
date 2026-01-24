DROP TABLE ticker;

CREATE TABLE IF NOT EXISTS ticker (
    time DATETIME PRIMARY KEY,
    bid FLOAT,
    ask FLOAT
);