SELECT * FROM songs INDEXED BY idx_song_name;

-- transaction_sql = """
-- BEGIN TRANSACTION;
-- DELETE FROM current_songs;
-- INSERT INTO current_songs (song) SELECT song_name FROM songs WHERE current = 1;
-- COMMIT;
-- """

CREATE TABLE IF NOT EXISTS current_songs (
  song TEXT,
  season TEXT
)

CREATE INDEX IF NOT EXISTS idx_song ON current_songs (song);

SELECT * FROM current_songs INDEXED BY idx_song;

SELECT * FROM songs INDEXED BY idx_song_name WHERE current = 1;

-- 1. Set all songs.current = 0 (mark all as non-current)
UPDATE songs SET current = 0;

-- 2. Mark songs as current (current = 1) for all songs listed in current_songs table
UPDATE songs 
SET current = 1 
WHERE song_name IN (SELECT song FROM current_songs);

-- Combined transaction approach:
BEGIN TRANSACTION;
UPDATE songs SET current = 0;
UPDATE songs SET current = 1 WHERE song_name IN (SELECT song FROM current_songs);
COMMIT;

-- Alternative using JOIN syntax:
UPDATE songs 
SET current = 1 
FROM current_songs cs 
WHERE songs.song_name = cs.song;

select song_name from songs where current = 1;

select* from songs where 