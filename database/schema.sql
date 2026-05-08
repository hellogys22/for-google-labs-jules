-- Enable pgvector extension
create extension if not exists vector;

-- Create products table
create table products (
  id uuid primary key,
  name text not null,
  price numeric not null,
  platform text not null,
  rating numeric,
  affiliate_url text,
  image_url text,
  video_path text,
  embedding vector(1536),
  performance_score numeric default 0.5,
  created_at timestamp with time zone default timezone('utc'::text, now()) not null
);

-- Create reels table
create table reels (
  id uuid primary key default gen_random_uuid(),
  product_id uuid references products(id),
  script_json jsonb,
  video_path text,
  audio_path text,
  status text default 'ready',
  instagram_post_id text,
  posted_at timestamp with time zone,
  created_at timestamp with time zone default timezone('utc'::text, now()) not null
);

-- Create earnings table
create table earnings (
  id uuid primary key default gen_random_uuid(),
  date date not null,
  platform text not null,
  clicks integer default 0,
  conversions integer default 0,
  commission_inr numeric default 0,
  created_at timestamp with time zone default timezone('utc'::text, now()) not null
);

-- Create daily_reports table
create table daily_reports (
  id uuid primary key default gen_random_uuid(),
  date date not null,
  total_clicks integer default 0,
  total_conversions integer default 0,
  total_commission_inr numeric default 0,
  best_product text,
  worst_product text,
  created_at timestamp with time zone default timezone('utc'::text, now()) not null
);

-- Create agent_logs table
create table agent_logs (
  id uuid primary key default gen_random_uuid(),
  agent_name text not null,
  status text not null,
  message text,
  created_at timestamp with time zone default timezone('utc'::text, now()) not null
);

-- Create RAG match_products function
create or replace function match_products (
  query_embedding vector(1536),
  match_count int default 3
) returns table (
  id uuid,
  name text,
  price numeric,
  platform text,
  image_url text,
  similarity float
)
language sql
as $$
  select
    id,
    name,
    price,
    platform,
    image_url,
    1 - (products.embedding <=> query_embedding) as similarity
  from products
  order by products.embedding <=> query_embedding
  limit match_count;
$$;