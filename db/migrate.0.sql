CREATE TABLE hints (post_id primary_key, content text);
CREATE TABLE bodies (post_id primary_key, content text, header text);
CREATE TABLE posts (id integer primary key, title text not null, tags text not null, draft integer DEFAULT 0, publish_date date DEFAULT '2100-01-01', difficulty text, subtitle text);
