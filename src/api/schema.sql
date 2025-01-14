create table
  public.inventory (
    id bigint generated by default as identity,
    gold bigint not null,
    constraint inventory_pkey primary key (id),
    constraint inventory_id_key unique (id)
  ) tablespace pg_default;

create table
  public.liquids (
    quantity integer not null default 0,
    type integer[] not null,
    id bigint generated by default as identity,
    constraint liquids_pkey primary key (id)
  ) tablespace pg_default;

create table
  public.potions (
    sku text not null,
    quantity integer not null default 0,
    type integer[] not null,
    constraint Potions_pkey primary key (sku),
    constraint Potions_sku_key unique (sku)
  ) tablespace pg_default;

create table
  public.carts (
    id bigint generated by default as identity,
    customer_name text null,
    payment text null,
    timestamp timestamp with time zone not null default now(),
    constraint newcarts_pkey primary key (id),
    constraint newcarts_id_key unique (id)
  ) tablespace pg_default;

create table
  public.cart_items (
    id bigint generated by default as identity,
    cart_fkey bigint not null,
    potions_fkey text not null,
    quantity integer null,
    constraint cart_items_pkey primary key (id),
    constraint cart_items_cart_fkey_fkey foreign key (cart_fkey) references carts (id),
    constraint cart_items_potions_fkey_fkey foreign key (potions_fkey) references potions (sku)
  ) tablespace pg_default;