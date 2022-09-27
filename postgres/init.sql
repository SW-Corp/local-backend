CREATE TYPE component_kind AS ENUM ('valve', 'pump', 'tank');
CREATE TYPE component_mode AS ENUM ('manual', 'automatic');
CREATE TYPE metric_type AS ENUM('water_level', 'is_open', 'voltage', 'current', 'is_on', 'float_switch_up', 'pressure');
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
	name varchar not null unique,
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

CREATE TABLE public.tanks_offset(
	id SERIAL PRIMARY KEY,
	component_name varchar not null,
	offset_ real not null,
	foreign key (component_name) references components(name)
);


INSERT INTO public.users (email, password, permission)
	VALUES 
	('user@email.com','$2b$12$yOaeOCNaJybzzO7s13W06ur7bY4E82L.JdKJOkxfqHdY1EXT3Brh.', 'manage_users'),
	('connector', '$2b$12$CsC/b7s06OjwglB9.4ivWuZfLLiLnizk85RnU.jKoKcaurWfme4oW', 'write');

INSERT INTO public.workstations (name, display_name, description ,connector_address ,connector_port)
	VALUES ('testworkstation', 'Testowa stacja', 'test', 'connector', 7000);

INSERT INTO public.components (name, display_name, component_type, workstation)
	VALUES 
	('C1', 'Tank 1', 'tank', 'testworkstation'),
	('C2', 'Tank 2', 'tank', 'testworkstation'),
	('C3', 'Tank 1', 'tank', 'testworkstation'),
	('C4', 'Tank 2', 'tank', 'testworkstation'),
	('C5', 'Tank 1', 'tank', 'testworkstation'),
	('V1', 'Valve 1', 'valve', 'testworkstation'),
	('V2', 'Valve 2', 'valve', 'testworkstation'),
	('V3', 'Valve 3', 'valve', 'testworkstation'),
	('P1', 'Pump 1', 'pump', 'testworkstation'),
	('P2', 'Pump 2', 'pump', 'testworkstation'),
	('P3', 'Pump 3', 'pump', 'testworkstation'),
	('P4', 'Pump 4', 'pump', 'testworkstation');

INSERT INTO public.metrics (metric_type, component_type)
	VALUES
	('float_switch_up', 'tank'),
	('pressure', 'tank'),
	('water_level', 'tank'),
	('current', 'pump'),
	('voltage', 'pump'),
	('is_on', 'pump'),
	('current', 'valve'),
	('voltage', 'valve'),
	('is_open', 'valve');

INSERT INTO public.tanks_offset (component_name, offset_)
	VALUES
	('C1', -1.5),
	('C2', 1.5),
	('C3', -2.27),
	('C4', 0),
	('C5', -1);
