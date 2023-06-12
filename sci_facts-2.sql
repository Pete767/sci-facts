/* this file no longer relavent. is kept to see what i started with.*/

CREATE DATABASE sci_facts;

\c sci_facts

CREATE TYPE "media" AS ENUM (
  'book',
  'movie',
  'comic',
  'tv series',
  'radio',
  'game'
);

CREATE TYPE "q_or_f" AS ENUM (
  'quote',
  'fact'
);

CREATE TYPE "status_type" AS ENUM (
  'approved',
  'rejected',
  'pending'
);

CREATE TABLE "facts" (
  "fact_id" serial PRIMARY KEY,
  "source_id" integer,
  "fact" text
);

CREATE TABLE "users" (
  "id" serial PRIMARY KEY,
  "username" varchar UNIQUE,
  "admin" boolean,
  "password" varchar,
  "favorites" integer,
  "email" varchar
);

CREATE TABLE "submition" (
  "id" serial PRIMARY KEY,
  "source" varchar,
  "body" text,
  "username" varchar,
  "status" status_type,
  "created_at" timestamp,
  "quote_or_fact" q_or_f
);

CREATE TABLE "source" (
  "id" serial PRIMARY KEY,
  "source_name" varchar,
  "san_name" varchar,
  "media" media
);

CREATE TABLE "quotes" (
  "quote_id" serial PRIMARY KEY,
  "source_id" integer,
  "quote" text
);

ALTER TABLE "source" ADD FOREIGN KEY ("id") REFERENCES "facts" ("source_id");

ALTER TABLE "source" ADD FOREIGN KEY ("id") REFERENCES "quotes" ("source_id");

ALTER TABLE "source" ADD FOREIGN KEY ("id") REFERENCES "users" ("favorites");

ALTER TABLE "users" ADD FOREIGN KEY ("username") REFERENCES "submition" ("username");
