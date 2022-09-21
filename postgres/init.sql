CREATE TYPE component_kind AS ENUM ('valve', 'pump', 'tank');
CREATE TYPE component_mode AS ENUM ('manual', 'automatic');
CREATE TYPE metric_type AS ENUM('water_level', 'is_open');
CREATE TYPE permission_type AS ENUM('read', 'write', 'manage_users');
CREATE TABLE public.users (
	email varchar not NULL PRIMARY KEY,
	password varchar not NULL,
	permission permission_type not null
);

CREATE TABLE public.workstations (
	name varchar not NULL PRIMARY KEY,
	display_name varchar not NULL,
	description varchar not NULL,
	connector_address varchar NULL,
	connector_port int
);

CREATE TABLE public.components(
	component_id SERIAL PRIMARY KEY,
	name varchar not null,
	display_name varchar,
	component_type component_kind not null,
	workstation varchar not null,
	foreign key (workstation) references workstations(name)
);

CREATE TABLE public.metrics(
	id SERIAL PRIMARY KEY,
	metric_type metric_type not null,
	component_type component_kind not null

);

INSERT INTO public.users (email, password, permission)
	VALUES ('user@email.com','$2b$12$yOaeOCNaJybzzO7s13W06ur7bY4E82L.JdKJOkxfqHdY1EXT3Brh.', 'manage_users');

INSERT INTO public.workstations (name, display_name, description ,connector_address ,connector_port)
	VALUES ('testworkstation', 'Testowa stacja', 'test', 'connector', 7000);

INSERT INTO public.components (name, display_name, component_type, workstation)
	VALUES 
	('tank1', 'Tank 1', 'tank', 'testworkstation'),
	('tank2', 'Tank 2', 'tank', 'testworkstation'),
	('valve2', 'Valve 2', 'valve', 'testworkstation'),
	('valve2', 'Valve 2', 'valve', 'testworkstation');

INSERT INTO public.metrics (metric_type, component_type)
	VALUES
	('water_level', 'tank'),
	('is_open', 'valve');
