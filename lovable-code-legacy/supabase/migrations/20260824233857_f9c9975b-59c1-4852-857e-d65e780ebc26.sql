-- =========================================================
-- ESP-PMM governed engineering master data (Asset ConneX)
-- =========================================================

CREATE TABLE public.esp_oems (
  id text PRIMARY KEY,
  name text NOT NULL,
  legal_note text,
  lifecycle_status text NOT NULL DEFAULT 'current',
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now()
);
GRANT SELECT ON public.esp_oems TO anon, authenticated;
GRANT ALL ON public.esp_oems TO service_role;
ALTER TABLE public.esp_oems ENABLE ROW LEVEL SECURITY;
CREATE POLICY "esp_oems public read" ON public.esp_oems FOR SELECT TO anon, authenticated USING (true);

CREATE TABLE public.esp_sources (
  id text PRIMARY KEY,
  title text NOT NULL,
  publisher text NOT NULL,
  source_type text NOT NULL,
  document_ref text,
  document_date text,
  revision text,
  reliability_code text NOT NULL,
  usage_rights_status text NOT NULL DEFAULT 'internal-reference-only',
  verification_status text NOT NULL DEFAULT 'unverified',
  last_review_date date,
  notes text,
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now()
);
GRANT SELECT ON public.esp_sources TO anon, authenticated;
GRANT ALL ON public.esp_sources TO service_role;
ALTER TABLE public.esp_sources ENABLE ROW LEVEL SECURITY;
CREATE POLICY "esp_sources public read" ON public.esp_sources FOR SELECT TO anon, authenticated USING (true);

CREATE TABLE public.esp_pump_models (
  id text PRIMARY KEY,
  oem_id text NOT NULL REFERENCES public.esp_oems(id),
  brand_line text,
  series text,
  model text NOT NULL,
  model_revision text,
  lifecycle_status text NOT NULL DEFAULT 'current',
  stage_geometry text,
  construction_type text,
  od_in numeric,
  min_casing_in numeric,
  reference_hz numeric,
  reference_rpm numeric,
  ror_min_bpd numeric,
  ror_max_bpd numeric,
  bep_flow_bpd numeric,
  bep_head_ft_per_stage numeric,
  bep_power_hp_per_stage numeric,
  bep_efficiency_pct numeric,
  housing_burst_psi numeric,
  shaft_diameter_in numeric,
  shaft_material text,
  stage_material text,
  bearing_material text,
  shaft_hp_limit numeric,
  temperature_note text,
  application_note text,
  curve_completeness text NOT NULL DEFAULT 'none',
  source_id text REFERENCES public.esp_sources(id),
  reliability_code text NOT NULL DEFAULT 'D',
  usage_rights_status text NOT NULL DEFAULT 'internal-reference-only',
  verification_status text NOT NULL DEFAULT 'unverified',
  last_review_date date,
  cced_installed_count integer NOT NULL DEFAULT 0,
  wsw_design_min_bpd numeric,
  wsw_design_max_bpd numeric,
  wsw_crosscheck_result text,
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now()
);
GRANT SELECT ON public.esp_pump_models TO anon, authenticated;
GRANT ALL ON public.esp_pump_models TO service_role;
ALTER TABLE public.esp_pump_models ENABLE ROW LEVEL SECURITY;
CREATE POLICY "esp_pump_models public read" ON public.esp_pump_models FOR SELECT TO anon, authenticated USING (true);

CREATE TABLE public.esp_pump_curve_points (
  id bigserial PRIMARY KEY,
  pump_model_id text NOT NULL REFERENCES public.esp_pump_models(id) ON DELETE CASCADE,
  curve_revision text NOT NULL DEFAULT 'R0',
  reference_hz numeric NOT NULL,
  reference_rpm numeric,
  stage_basis text NOT NULL DEFAULT 'per-stage',
  flow_bpd numeric NOT NULL,
  head_ft_per_stage numeric,
  power_hp_per_stage numeric,
  efficiency_pct numeric,
  point_sequence integer NOT NULL,
  source_id text REFERENCES public.esp_sources(id),
  extraction_method text,
  confidence numeric,
  created_at timestamptz NOT NULL DEFAULT now()
);
GRANT SELECT ON public.esp_pump_curve_points TO anon, authenticated;
GRANT ALL ON public.esp_pump_curve_points TO service_role;
ALTER TABLE public.esp_pump_curve_points ENABLE ROW LEVEL SECURITY;
CREATE POLICY "esp_pump_curve_points public read" ON public.esp_pump_curve_points FOR SELECT TO anon, authenticated USING (true);
CREATE INDEX esp_curve_points_model_idx ON public.esp_pump_curve_points (pump_model_id, reference_hz, point_sequence);

CREATE TABLE public.esp_motor_models (
  id text PRIMARY KEY,
  oem_id text NOT NULL REFERENCES public.esp_oems(id),
  series text,
  model text NOT NULL,
  od_in numeric,
  nameplate_hp numeric,
  nameplate_volts numeric,
  nameplate_amps numeric,
  winding_type text,
  max_temp_f numeric,
  construction_note text,
  source_id text REFERENCES public.esp_sources(id),
  reliability_code text NOT NULL DEFAULT 'D',
  verification_status text NOT NULL DEFAULT 'unverified',
  cced_installed_count integer NOT NULL DEFAULT 0,
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now()
);
GRANT SELECT ON public.esp_motor_models TO anon, authenticated;
GRANT ALL ON public.esp_motor_models TO service_role;
ALTER TABLE public.esp_motor_models ENABLE ROW LEVEL SECURITY;
CREATE POLICY "esp_motor_models public read" ON public.esp_motor_models FOR SELECT TO anon, authenticated USING (true);

CREATE TABLE public.esp_gas_handling_models (
  id text PRIMARY KEY,
  oem_id text NOT NULL REFERENCES public.esp_oems(id),
  model text NOT NULL,
  device_type text NOT NULL,
  od_in numeric,
  max_gvf_pct numeric,
  max_flow_bpd numeric,
  source_id text REFERENCES public.esp_sources(id),
  reliability_code text NOT NULL DEFAULT 'D',
  verification_status text NOT NULL DEFAULT 'unverified',
  cced_installed_count integer NOT NULL DEFAULT 0,
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now()
);
GRANT SELECT ON public.esp_gas_handling_models TO anon, authenticated;
GRANT ALL ON public.esp_gas_handling_models TO service_role;
ALTER TABLE public.esp_gas_handling_models ENABLE ROW LEVEL SECURITY;
CREATE POLICY "esp_gas_handling public read" ON public.esp_gas_handling_models FOR SELECT TO anon, authenticated USING (true);

CREATE TABLE public.esp_protector_models (
  id text PRIMARY KEY,
  oem_id text NOT NULL REFERENCES public.esp_oems(id),
  model text NOT NULL,
  configuration text,
  od_in numeric,
  thrust_bearing_rating_lbf numeric,
  chamber_count integer,
  elastomer text,
  source_id text REFERENCES public.esp_sources(id),
  reliability_code text NOT NULL DEFAULT 'D',
  verification_status text NOT NULL DEFAULT 'unverified',
  cced_installed_count integer NOT NULL DEFAULT 0,
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now()
);
GRANT SELECT ON public.esp_protector_models TO anon, authenticated;
GRANT ALL ON public.esp_protector_models TO service_role;
ALTER TABLE public.esp_protector_models ENABLE ROW LEVEL SECURITY;
CREATE POLICY "esp_protector public read" ON public.esp_protector_models FOR SELECT TO anon, authenticated USING (true);

CREATE TABLE public.esp_cable_models (
  id text PRIMARY KEY,
  oem_id text NOT NULL REFERENCES public.esp_oems(id),
  model text NOT NULL,
  conductor_size_awg text,
  cable_type text,
  armor text,
  max_temp_f numeric,
  voltage_rating_v numeric,
  resistance_ohm_per_kft numeric,
  source_id text REFERENCES public.esp_sources(id),
  reliability_code text NOT NULL DEFAULT 'D',
  verification_status text NOT NULL DEFAULT 'unverified',
  cced_installed_count integer NOT NULL DEFAULT 0,
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now()
);
GRANT SELECT ON public.esp_cable_models TO anon, authenticated;
GRANT ALL ON public.esp_cable_models TO service_role;
ALTER TABLE public.esp_cable_models ENABLE ROW LEVEL SECURITY;
CREATE POLICY "esp_cable public read" ON public.esp_cable_models FOR SELECT TO anon, authenticated USING (true);

CREATE TABLE public.esp_vsd_models (
  id text PRIMARY KEY,
  oem_id text NOT NULL REFERENCES public.esp_oems(id),
  model text NOT NULL,
  drive_type text,
  kva_rating numeric,
  output_amps numeric,
  output_volts numeric,
  transformer_note text,
  source_id text REFERENCES public.esp_sources(id),
  reliability_code text NOT NULL DEFAULT 'D',
  verification_status text NOT NULL DEFAULT 'unverified',
  cced_installed_count integer NOT NULL DEFAULT 0,
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now()
);
GRANT SELECT ON public.esp_vsd_models TO anon, authenticated;
GRANT ALL ON public.esp_vsd_models TO service_role;
ALTER TABLE public.esp_vsd_models ENABLE ROW LEVEL SECURITY;
CREATE POLICY "esp_vsd public read" ON public.esp_vsd_models FOR SELECT TO anon, authenticated USING (true);

CREATE TABLE public.esp_sensor_models (
  id text PRIMARY KEY,
  oem_id text NOT NULL REFERENCES public.esp_oems(id),
  model text NOT NULL,
  measured_channels text,
  max_temp_f numeric,
  pressure_rating_psi numeric,
  source_id text REFERENCES public.esp_sources(id),
  reliability_code text NOT NULL DEFAULT 'D',
  verification_status text NOT NULL DEFAULT 'unverified',
  cced_installed_count integer NOT NULL DEFAULT 0,
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now()
);
GRANT SELECT ON public.esp_sensor_models TO anon, authenticated;
GRANT ALL ON public.esp_sensor_models TO service_role;
ALTER TABLE public.esp_sensor_models ENABLE ROW LEVEL SECURITY;
CREATE POLICY "esp_sensor public read" ON public.esp_sensor_models FOR SELECT TO anon, authenticated USING (true);

-- ---------------------------------------------------------
-- Installed fleet
-- ---------------------------------------------------------

CREATE TABLE public.esp_fields (
  id text PRIMARY KEY,
  enterprise text NOT NULL,
  name text NOT NULL,
  region text,
  block text,
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now()
);
GRANT SELECT ON public.esp_fields TO anon, authenticated;
GRANT ALL ON public.esp_fields TO service_role;
ALTER TABLE public.esp_fields ENABLE ROW LEVEL SECURITY;
CREATE POLICY "esp_fields public read" ON public.esp_fields FOR SELECT TO anon, authenticated USING (true);

CREATE TABLE public.esp_wells (
  id text PRIMARY KEY,
  field_id text NOT NULL REFERENCES public.esp_fields(id),
  pad_area text,
  name text NOT NULL,
  lift_method text NOT NULL DEFAULT 'ESP',
  well_status text NOT NULL DEFAULT 'producing',
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now()
);
GRANT SELECT ON public.esp_wells TO anon, authenticated;
GRANT ALL ON public.esp_wells TO service_role;
ALTER TABLE public.esp_wells ENABLE ROW LEVEL SECURITY;
CREATE POLICY "esp_wells public read" ON public.esp_wells FOR SELECT TO anon, authenticated USING (true);

CREATE TABLE public.esp_installed_systems (
  id text PRIMARY KEY,
  well_id text NOT NULL REFERENCES public.esp_wells(id) ON DELETE CASCADE,
  raw_designation text,
  normalized_pump_model_id text REFERENCES public.esp_pump_models(id),
  assembly_type text NOT NULL DEFAULT 'single',
  motor_model_id text REFERENCES public.esp_motor_models(id),
  gas_handling_model_id text REFERENCES public.esp_gas_handling_models(id),
  protector_model_id text REFERENCES public.esp_protector_models(id),
  cable_model_id text REFERENCES public.esp_cable_models(id),
  vsd_model_id text REFERENCES public.esp_vsd_models(id),
  sensor_model_id text REFERENCES public.esp_sensor_models(id),
  total_stages integer,
  design_hz numeric,
  operating_hz numeric,
  install_date date,
  run_life_days integer,
  match_confidence numeric,
  match_status text NOT NULL DEFAULT 'matched',
  unresolved_note text,
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now()
);
GRANT SELECT ON public.esp_installed_systems TO anon, authenticated;
GRANT ALL ON public.esp_installed_systems TO service_role;
ALTER TABLE public.esp_installed_systems ENABLE ROW LEVEL SECURITY;
CREATE POLICY "esp_installed_systems public read" ON public.esp_installed_systems FOR SELECT TO anon, authenticated USING (true);

CREATE TABLE public.esp_installed_pump_sections (
  id text PRIMARY KEY,
  installed_system_id text NOT NULL REFERENCES public.esp_installed_systems(id) ON DELETE CASCADE,
  section_sequence integer NOT NULL,
  pump_model_id text REFERENCES public.esp_pump_models(id),
  raw_designation text,
  stages integer,
  stages_known boolean NOT NULL DEFAULT true,
  note text,
  created_at timestamptz NOT NULL DEFAULT now()
);
GRANT SELECT ON public.esp_installed_pump_sections TO anon, authenticated;
GRANT ALL ON public.esp_installed_pump_sections TO service_role;
ALTER TABLE public.esp_installed_pump_sections ENABLE ROW LEVEL SECURITY;
CREATE POLICY "esp_sections public read" ON public.esp_installed_pump_sections FOR SELECT TO anon, authenticated USING (true);

CREATE TABLE public.esp_well_engineering (
  well_id text PRIMARY KEY REFERENCES public.esp_wells(id) ON DELETE CASCADE,
  casing_od_in numeric,
  casing_weight_lb_ft numeric,
  tubing_id_in numeric,
  pump_setting_depth_ft numeric,
  perf_top_ft numeric,
  perf_bottom_ft numeric,
  deviation_at_pump_deg numeric,
  reservoir_pressure_psi numeric,
  productivity_index_bpd_psi numeric,
  bht_f numeric,
  source_id text REFERENCES public.esp_sources(id),
  reliability_code text NOT NULL DEFAULT 'D',
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now()
);
GRANT SELECT ON public.esp_well_engineering TO anon, authenticated;
GRANT ALL ON public.esp_well_engineering TO service_role;
ALTER TABLE public.esp_well_engineering ENABLE ROW LEVEL SECURITY;
CREATE POLICY "esp_well_eng public read" ON public.esp_well_engineering FOR SELECT TO anon, authenticated USING (true);

CREATE TABLE public.esp_fluid_pvt (
  well_id text PRIMARY KEY REFERENCES public.esp_wells(id) ON DELETE CASCADE,
  oil_api numeric,
  water_sg numeric,
  gas_sg numeric,
  water_cut_pct numeric,
  gor_scf_stb numeric,
  bubble_point_psi numeric,
  viscosity_cp numeric,
  h2s_ppm numeric,
  co2_pct numeric,
  sample_date date,
  source_id text REFERENCES public.esp_sources(id),
  reliability_code text NOT NULL DEFAULT 'D',
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now()
);
GRANT SELECT ON public.esp_fluid_pvt TO anon, authenticated;
GRANT ALL ON public.esp_fluid_pvt TO service_role;
ALTER TABLE public.esp_fluid_pvt ENABLE ROW LEVEL SECURITY;
CREATE POLICY "esp_fluid_pvt public read" ON public.esp_fluid_pvt FOR SELECT TO anon, authenticated USING (true);

CREATE TABLE public.esp_design_limits (
  well_id text PRIMARY KEY REFERENCES public.esp_wells(id) ON DELETE CASCADE,
  min_hz numeric,
  max_hz numeric,
  min_pip_psi numeric,
  max_motor_temp_f numeric,
  max_motor_load_pct numeric,
  max_vibration_g numeric,
  ror_min_bpd numeric,
  ror_max_bpd numeric,
  envelope_basis text,
  source_id text REFERENCES public.esp_sources(id),
  reliability_code text NOT NULL DEFAULT 'D',
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now()
);
GRANT SELECT ON public.esp_design_limits TO anon, authenticated;
GRANT ALL ON public.esp_design_limits TO service_role;
ALTER TABLE public.esp_design_limits ENABLE ROW LEVEL SECURITY;
CREATE POLICY "esp_design_limits public read" ON public.esp_design_limits FOR SELECT TO anon, authenticated USING (true);

CREATE TABLE public.esp_catalog_aliases (
  id text PRIMARY KEY,
  raw_designation text NOT NULL,
  entity_kind text NOT NULL DEFAULT 'pump',
  pump_model_id text REFERENCES public.esp_pump_models(id),
  normalized_oem_id text REFERENCES public.esp_oems(id),
  normalized_series text,
  normalized_model text,
  construction_variant text,
  mapping_status text NOT NULL DEFAULT 'mapped',
  cced_occurrences integer NOT NULL DEFAULT 0,
  note text,
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now()
);
GRANT SELECT ON public.esp_catalog_aliases TO anon, authenticated;
GRANT ALL ON public.esp_catalog_aliases TO service_role;
ALTER TABLE public.esp_catalog_aliases ENABLE ROW LEVEL SECURITY;
CREATE POLICY "esp_aliases public read" ON public.esp_catalog_aliases FOR SELECT TO anon, authenticated USING (true);

CREATE TABLE public.esp_data_quality_issues (
  id text PRIMARY KEY,
  title text NOT NULL,
  category text NOT NULL,
  severity text NOT NULL DEFAULT 'open',
  status text NOT NULL DEFAULT 'Open',
  scope text,
  raw_designation text,
  pump_model_id text REFERENCES public.esp_pump_models(id),
  affected_installations integer NOT NULL DEFAULT 0,
  detail text,
  required_action text,
  owner text,
  opened_at date,
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now()
);
GRANT SELECT ON public.esp_data_quality_issues TO anon, authenticated;
GRANT ALL ON public.esp_data_quality_issues TO service_role;
ALTER TABLE public.esp_data_quality_issues ENABLE ROW LEVEL SECURITY;
CREATE POLICY "esp_dq public read" ON public.esp_data_quality_issues FOR SELECT TO anon, authenticated USING (true);

CREATE OR REPLACE FUNCTION public.update_updated_at_column()
RETURNS TRIGGER AS $$ BEGIN NEW.updated_at = now(); RETURN NEW; END; $$ LANGUAGE plpgsql SET search_path = public;

CREATE TRIGGER esp_pump_models_updated BEFORE UPDATE ON public.esp_pump_models FOR EACH ROW EXECUTE FUNCTION public.update_updated_at_column();
CREATE TRIGGER esp_installed_systems_updated BEFORE UPDATE ON public.esp_installed_systems FOR EACH ROW EXECUTE FUNCTION public.update_updated_at_column();

-- =========================================================
-- SEED — CCED Block 3 reconciled catalog + fleet sample
-- =========================================================

INSERT INTO public.esp_oems (id, name, legal_note, lifecycle_status) VALUES
 ('borets','Borets','Current OEM','current'),
 ('bhce','Baker Hughes CENtrilift','Current OEM (CENtrilift product heritage)','current'),
 ('ge-wood','GE Oil & Gas / Wood Group ESP','Legacy OEM lineage; current support ownership unresolved','legacy'),
 ('slb-reda','SLB REDA','Current OEM','current'),
 ('alkhorayef','Alkhorayef Petroleum','Current OEM','current'),
 ('levare','Levare','Current OEM','current'),
 ('championx','ChampionX','Current OEM','current');

INSERT INTO public.esp_sources (id, title, publisher, source_type, document_ref, document_date, revision, reliability_code, usage_rights_status, verification_status, last_review_date, notes) VALUES
 ('src-borets-cat','Borets ESP Product Catalog — Series 400/538 hydraulics','Borets','oem-catalog','BOR-CAT-ESP','2023','Rev C','A2','licensed-customer-supplied','verified','2026-07-14','Series/product level evidence for installed Borets hydraulics.'),
 ('src-borets-comp','Borets historical compression-pump ROR reference','Borets','oem-origin-historical','BOR-HIST-COMP','2016','—','B2','internal-reference-only','verified','2026-08-02','Used for the WSW design-capacity independent cross-check.'),
 ('src-bhce-ds','Baker Hughes FLEXPump family datasheets','Baker Hughes','oem-datasheet','BH-FLEX-DS','2024','Rev 2','A1','public-oem-published','verified','2026-08-10',NULL),
 ('src-ge-wood-cat','GE Oil & Gas / Wood Group ESP catalog (historical)','GE Oil & Gas','oem-origin-historical','GEWG-ESP-CAT','2014','—','B2','internal-reference-only','partially-verified','2026-06-30','TD/TE families; current support ownership unresolved.'),
 ('src-spe-lit','SPE / artificial lift peer-reviewed and training references','SPE','peer-reviewed','SPE-AL-REF','2019','—','B1','licensed-customer-supplied','verified','2026-05-20',NULL),
 ('src-pengtools','Pengtools ESP model index','Pengtools','secondary-catalog','PT-ESP-IDX','2025','—','C1','discovery-only','unverified','2026-08-12','Discovery index only — must not be promoted to calculation grade.'),
 ('src-cced-wb','CCED Block 3 installed-fleet workbook','Customer (CCED)','customer-record','CCED-B3-ESP','2026-08','Reconciled','A2','licensed-customer-supplied','verified','2026-08-20','170 well rows, 169 populated ESP records, 31 hydraulic groups.'),
 ('src-unresolved','Unresolved / inferred placeholder','—','none',NULL,NULL,NULL,'D','not-usable','unverified',NULL,'Records requiring OEM verification before any calculation use.');

-- Pump models (installed counts from reconciled CCED workbook)
INSERT INTO public.esp_pump_models
 (id, oem_id, brand_line, series, model, model_revision, lifecycle_status, stage_geometry, construction_type, od_in, min_casing_in, reference_hz, reference_rpm,
  ror_min_bpd, ror_max_bpd, bep_flow_bpd, bep_head_ft_per_stage, bep_power_hp_per_stage, bep_efficiency_pct, housing_burst_psi, shaft_diameter_in, shaft_material,
  stage_material, bearing_material, shaft_hp_limit, temperature_note, application_note, curve_completeness, source_id, reliability_code, usage_rights_status,
  verification_status, last_review_date, cced_installed_count, wsw_design_min_bpd, wsw_design_max_bpd, wsw_crosscheck_result)
VALUES
 ('borets-400-400','borets','Borets ESP','400','400-400','R1','current','mixed-flow','compression',4.00,5.5,60,3500,250,600,400,22.0,0.28,62,5000,0.688,'Inconel 718','Ni-resist','Ni-resist',256,'Std ≤ 250 °F','Primary CCED workhorse hydraulic','full-curve','src-borets-cat','A2','licensed-customer-supplied','verified','2026-08-14',41,NULL,NULL,NULL),
 ('borets-400-1050','borets','Borets ESP','400','400-1050','R1','current','mixed-flow','compression',4.00,5.5,60,3500,700,1400,1050,18.5,0.62,66,5000,0.688,'Inconel 718','Ni-resist','Ni-resist',256,'Std ≤ 250 °F','High-rate CCED hydraulic','full-curve','src-borets-cat','A2','licensed-customer-supplied','verified','2026-08-14',27,NULL,NULL,NULL),
 ('gewood-td650','ge-wood','GE / Wood Group ESP','400','TD650',NULL,'legacy','mixed-flow','floater',4.00,5.5,60,3500,400,900,650,20.0,0.42,60,4500,0.625,'Monel','Ni-resist','Ni-resist',185,'Legacy rating','Legacy CCED installations; support ownership unresolved','bep-envelope-only','src-ge-wood-cat','B2','internal-reference-only','partially-verified','2026-06-30',13,NULL,NULL,NULL),
 ('borets-400-180','borets','Borets ESP','400','400-180','R1','current','radial','compression',4.00,5.5,60,3500,100,280,180,26.0,0.14,54,5000,0.688,'Inconel 718','Ni-resist','Ni-resist',256,'Std ≤ 250 °F','Low-rate CCED hydraulic','bep-envelope-only','src-borets-cat','A2','licensed-customer-supplied','verified','2026-08-14',11,NULL,NULL,NULL),
 ('borets-400-500','borets','Borets ESP','400','400-500','R1','current','mixed-flow','compression',4.00,5.5,60,3500,320,720,500,21.0,0.33,63,5000,0.688,'Inconel 718','Ni-resist','Ni-resist',256,'Std ≤ 250 °F',NULL,'bep-envelope-only','src-borets-cat','A2','licensed-customer-supplied','verified','2026-08-14',10,NULL,NULL,NULL),
 ('bhce-flexpumper','bhce','CENtrilift FLEXPump','400','FLEXPumpER',NULL,'current','mixed-flow','SSD (where stated)',4.00,5.5,60,3500,300,1100,700,19.0,0.45,64,5000,0.688,'Inconel','Ni-resist','Ni-resist',240,'Abrasion-resistant application','Wide-range abrasion-tolerant hydraulic','bep-envelope-only','src-bhce-ds','A1','public-oem-published','verified','2026-08-10',7,NULL,NULL,NULL),
 ('borets-400-750','borets','Borets ESP','400','400-750','R1','current','mixed-flow','compression',4.00,5.5,60,3500,500,1000,750,19.5,0.46,65,5000,0.688,'Inconel 718','Ni-resist','Ni-resist',256,'Std ≤ 250 °F','Component of CCED composite/tapered assembly','bep-envelope-only','src-borets-cat','A2','licensed-customer-supplied','verified','2026-08-14',7,NULL,NULL,NULL),
 ('gewood-td460','ge-wood','GE / Wood Group ESP','400','TD460',NULL,'legacy','mixed-flow','floater',4.00,5.5,60,3500,280,650,460,21.5,0.31,58,4500,0.625,'Monel','Ni-resist','Ni-resist',185,'Legacy rating','Legacy CCED installations','bep-envelope-only','src-ge-wood-cat','B2','internal-reference-only','partially-verified','2026-06-30',7,NULL,NULL,NULL),
 ('borets-538-3600','borets','Borets ESP','538','538-3600','R1','current','mixed-flow','compression',5.38,7.0,60,3500,1509,4600,3600,14.0,1.55,68,5000,0.875,'Inconel 718','Ni-resist','Ni-resist',400,'Std ≤ 250 °F','WSW design-capacity cross-check case','bep-envelope-only','src-borets-comp','B2','internal-reference-only','verified','2026-08-02',3,1509,4600,'MATCH'),
 ('borets-538-5000','borets','Borets ESP','538','538-5000','R1','current','mixed-flow','compression',5.38,7.0,60,3500,1509,6350,5000,12.5,2.05,69,5000,0.875,'Inconel 718','Ni-resist','Ni-resist',400,'Std ≤ 250 °F','WSW design-capacity cross-check case','bep-envelope-only','src-borets-comp','B2','internal-reference-only','verified','2026-08-02',4,1509,6350,'MATCH'),
 ('borets-538-7000','borets','Borets ESP','538','538-7000','R1','current','mixed-flow','compression',5.38,7.0,60,3500,1962,10000,7000,11.0,2.80,70,5000,0.875,'Inconel 718','Ni-resist','Ni-resist',400,'Std ≤ 250 °F','WSW design-capacity cross-check case','bep-envelope-only','src-borets-comp','B2','internal-reference-only','verified','2026-08-02',3,1962,10000,'MATCH'),
 ('borets-538-9000','borets','Borets ESP','538','538-9000','R1','current','mixed-flow','compression',5.38,7.0,60,3500,3019,11000,9000,10.0,3.40,70,5000,0.875,'Inconel 718','Ni-resist','Ni-resist',400,'Std ≤ 250 °F','WSW design-capacity cross-check case','bep-envelope-only','src-borets-comp','B2','internal-reference-only','verified','2026-08-02',2,3019,11000,'MATCH'),
 ('borets-400-1750','borets','Borets ESP','400','B400-1750','R1','current','mixed-flow','compression',4.00,5.5,60,3500,1000,2400,1750,15.0,0.95,66,5000,0.688,'Inconel 718','Ni-resist','Ni-resist',256,'Std ≤ 250 °F','WSW design-capacity cross-check case','bep-envelope-only','src-borets-comp','B2','internal-reference-only','verified','2026-08-02',5,1000,2400,'MATCH'),
 ('bhce-flexpump10','bhce','CENtrilift FLEXPump','400','FLEXPump10 SSD',NULL,'current','mixed-flow','SSD',4.00,5.5,60,3500,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,'FLEX10 family; hydraulic detail pending OEM confirmation','curve-pending','src-bhce-ds','A1','public-oem-published','partially-verified','2026-08-10',2,NULL,NULL,NULL),
 ('bhce-flex21','bhce','CENtrilift FLEXPump','400','FLEX2.1',NULL,'current',NULL,NULL,4.00,5.5,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,'Designation preserved as recorded; OEM verification pending','none','src-cced-wb','C1','discovery-only','unverified','2026-08-20',1,NULL,NULL,NULL),
 ('bhce-400pm-unresolved','bhce','CENtrilift PM construction','400','400PM (construction family only)',NULL,'current',NULL,'SSD / SND / SHD as recorded',4.00,5.5,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,'Exact hydraulic P-model NOT stated — do not infer P4/P6/P10','none','src-unresolved','D','not-usable','unverified','2026-08-20',4,NULL,NULL,NULL),
 ('bhce-flexssd-unresolved','bhce','CENtrilift FLEXPump','400','FLEX SSD (family only)',NULL,'current',NULL,'SSD',4.00,5.5,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,'FLEX family known; exact hydraulic model missing','none','src-unresolved','D','not-usable','unverified','2026-08-20',1,NULL,NULL,NULL),
 ('gewood-te2700','ge-wood','GE / Wood Group ESP','538','TE2700',NULL,'legacy','mixed-flow','floater',5.38,7.0,60,3500,1500,3600,2700,13.5,1.25,64,4500,0.875,'Monel','Ni-resist','Ni-resist',375,'Legacy rating','Legacy CCED installation','bep-envelope-only','src-ge-wood-cat','B2','internal-reference-only','partially-verified','2026-06-30',4,NULL,NULL,NULL);

-- Curve points: digitised from the Borets catalog for the two full-curve models only.
INSERT INTO public.esp_pump_curve_points (pump_model_id, curve_revision, reference_hz, reference_rpm, stage_basis, flow_bpd, head_ft_per_stage, power_hp_per_stage, efficiency_pct, point_sequence, source_id, extraction_method, confidence) VALUES
 ('borets-400-400','R1',60,3500,'per-stage',0,32.0,0.16,0,1,'src-borets-cat','catalog-digitised',0.85),
 ('borets-400-400','R1',60,3500,'per-stage',150,29.5,0.20,42,2,'src-borets-cat','catalog-digitised',0.85),
 ('borets-400-400','R1',60,3500,'per-stage',250,27.0,0.24,55,3,'src-borets-cat','catalog-digitised',0.85),
 ('borets-400-400','R1',60,3500,'per-stage',330,24.6,0.26,60,4,'src-borets-cat','catalog-digitised',0.85),
 ('borets-400-400','R1',60,3500,'per-stage',400,22.0,0.28,62,5,'src-borets-cat','catalog-digitised',0.85),
 ('borets-400-400','R1',60,3500,'per-stage',480,18.8,0.30,59,6,'src-borets-cat','catalog-digitised',0.85),
 ('borets-400-400','R1',60,3500,'per-stage',600,12.5,0.32,48,7,'src-borets-cat','catalog-digitised',0.85),
 ('borets-400-400','R1',60,3500,'per-stage',700,6.0,0.33,32,8,'src-borets-cat','catalog-digitised',0.80),
 ('borets-400-400','R1',50,2917,'per-stage',0,22.2,0.09,0,1,'src-borets-cat','affinity-from-60Hz-catalog',0.70),
 ('borets-400-400','R1',50,2917,'per-stage',208,18.8,0.14,55,2,'src-borets-cat','affinity-from-60Hz-catalog',0.70),
 ('borets-400-400','R1',50,2917,'per-stage',333,15.3,0.16,62,3,'src-borets-cat','affinity-from-60Hz-catalog',0.70),
 ('borets-400-400','R1',50,2917,'per-stage',500,8.7,0.19,48,4,'src-borets-cat','affinity-from-60Hz-catalog',0.70),
 ('borets-400-1050','R1',60,3500,'per-stage',0,27.0,0.34,0,1,'src-borets-cat','catalog-digitised',0.85),
 ('borets-400-1050','R1',60,3500,'per-stage',400,24.5,0.44,45,2,'src-borets-cat','catalog-digitised',0.85),
 ('borets-400-1050','R1',60,3500,'per-stage',700,21.8,0.53,60,3,'src-borets-cat','catalog-digitised',0.85),
 ('borets-400-1050','R1',60,3500,'per-stage',900,19.8,0.58,65,4,'src-borets-cat','catalog-digitised',0.85),
 ('borets-400-1050','R1',60,3500,'per-stage',1050,18.5,0.62,66,5,'src-borets-cat','catalog-digitised',0.85),
 ('borets-400-1050','R1',60,3500,'per-stage',1200,16.2,0.65,62,6,'src-borets-cat','catalog-digitised',0.85),
 ('borets-400-1050','R1',60,3500,'per-stage',1400,11.5,0.68,52,7,'src-borets-cat','catalog-digitised',0.85),
 ('borets-400-1050','R1',60,3500,'per-stage',1600,5.5,0.70,34,8,'src-borets-cat','catalog-digitised',0.80);

INSERT INTO public.esp_motor_models (id, oem_id, series, model, od_in, nameplate_hp, nameplate_volts, nameplate_amps, winding_type, max_temp_f, construction_note, source_id, reliability_code, verification_status, cced_installed_count) VALUES
 ('borets-m456-120','borets','456','456 120HP',4.56,120,1350,56,'Ester/PEEK',400,'Single section','src-borets-cat','A2','verified',38),
 ('borets-m456-180','borets','456','456 180HP',4.56,180,2050,55,'Ester/PEEK',400,'Tandem upper/lower','src-borets-cat','A2','verified',26),
 ('bhce-m450-150','bhce','450','450 150HP',4.50,150,1700,55,'Std',400,NULL,'src-bhce-ds','A1','verified',9),
 ('gewood-m456-100','ge-wood','456','456 100HP',4.56,100,1180,52,'Legacy',350,'Legacy motor','src-ge-wood-cat','B2','partially-verified',14);

INSERT INTO public.esp_gas_handling_models (id, oem_id, model, device_type, od_in, max_gvf_pct, max_flow_bpd, source_id, reliability_code, verification_status, cced_installed_count) VALUES
 ('borets-gs400','borets','400 Rotary Gas Separator','gas-separator',4.00,45,3000,'src-borets-cat','A2','verified',44),
 ('borets-gh400','borets','400 Advanced Gas Handler','gas-handler',4.00,60,2500,'src-borets-cat','A2','verified',19),
 ('bhce-gh400','bhce','400 Gas Handler','gas-handler',4.00,55,2200,'src-bhce-ds','A1','verified',6);

INSERT INTO public.esp_protector_models (id, oem_id, model, configuration, od_in, thrust_bearing_rating_lbf, chamber_count, elastomer, source_id, reliability_code, verification_status, cced_installed_count) VALUES
 ('borets-p400-lsbpb','borets','400 LSBPB','Labyrinth + bag, series',4.00,7500,2,'HSN','src-borets-cat','A2','verified',52),
 ('bhce-p400-bpbsl','bhce','400 BPBSL','Bag + labyrinth',4.00,7000,2,'Aflas','src-bhce-ds','A1','verified',8),
 ('gewood-p400-legacy','ge-wood','400 legacy seal section','Labyrinth',4.00,6000,1,'Nitrile','src-ge-wood-cat','B2','partially-verified',12);

INSERT INTO public.esp_cable_models (id, oem_id, model, conductor_size_awg, cable_type, armor, max_temp_f, voltage_rating_v, resistance_ohm_per_kft, source_id, reliability_code, verification_status, cced_installed_count) VALUES
 ('borets-cbl-1awg','borets','Flat EPDM/Lead 1 AWG','1','flat','Galvanised',400,5000,0.128,'src-borets-cat','A2','verified',47),
 ('borets-cbl-4awg','borets','Round EPDM 4 AWG','4','round','Galvanised',400,5000,0.259,'src-borets-cat','A2','verified',21),
 ('bhce-cbl-2awg','bhce','CENtrilift flat 2 AWG','2','flat','Monel',450,5000,0.162,'src-bhce-ds','A1','verified',10);

INSERT INTO public.esp_vsd_models (id, oem_id, model, drive_type, kva_rating, output_amps, output_volts, transformer_note, source_id, reliability_code, verification_status, cced_installed_count) VALUES
 ('borets-vsd-260','borets','Borets VSD 260 kVA','6-pulse',260,110,2400,'Step-up SUT 300 kVA','src-borets-cat','A2','verified',63),
 ('bhce-vsd-electrospeed','bhce','Electrospeed Advantage','6-pulse',350,150,2400,'Integrated SUT','src-bhce-ds','A1','verified',12),
 ('gewood-vsd-legacy','ge-wood','Legacy GE drive','6-pulse',200,90,2400,'External SUT','src-ge-wood-cat','B2','partially-verified',9);

INSERT INTO public.esp_sensor_models (id, oem_id, model, measured_channels, max_temp_f, pressure_rating_psi, source_id, reliability_code, verification_status, cced_installed_count) VALUES
 ('borets-gauge-std','borets','Borets downhole gauge','PIP, PDP, motor temp, vibration, leakage',350,5000,'src-borets-cat','A2','verified',58),
 ('bhce-centinel','bhce','CENTINEL gauge','PIP, intake temp, motor temp, vibration',400,5000,'src-bhce-ds','A1','verified',11);

-- Alias normalisation (CCED raw designations)
INSERT INTO public.esp_catalog_aliases (id, raw_designation, entity_kind, pump_model_id, normalized_oem_id, normalized_series, normalized_model, construction_variant, mapping_status, cced_occurrences, note) VALUES
 ('al-b400-400','B400-400','pump','borets-400-400','borets','400','400-400',NULL,'mapped',41,NULL),
 ('al-400-1050','400-1050','pump','borets-400-1050','borets','400','400-1050',NULL,'mapped',18,NULL),
 ('al-b400-1050','B400-1050','pump','borets-400-1050','borets','400','400-1050',NULL,'mapped',9,NULL),
 ('al-400flexer','400FlexER','pump','bhce-flexpumper','bhce','400','FLEXPumpER',NULL,'mapped',3,NULL),
 ('al-flexer-space','Flex ER','pump','bhce-flexpumper','bhce','400','FLEXPumpER',NULL,'mapped',2,NULL),
 ('al-flexer','FlexER','pump','bhce-flexpumper','bhce','400','FLEXPumpER',NULL,'mapped',1,NULL),
 ('al-flexer-ssd','FlexER SSD','pump','bhce-flexpumper','bhce','400','FLEXPumpER','SSD','mapped',1,'Construction variant recorded.'),
 ('al-flex10-ssd','Flex10 SSD','pump','bhce-flexpump10','bhce','400','FLEXPump10','SSD','mapped',1,NULL),
 ('al-flexssd10','FlexSSD10','pump','bhce-flexpump10','bhce','400','FLEXPump10','SSD','mapped',1,NULL),
 ('al-td650','TD650','pump','gewood-td650','ge-wood','400','TD650',NULL,'mapped-legacy',13,'Legacy GE/Wood family; support ownership unresolved.'),
 ('al-td460','TD460','pump','gewood-td460','ge-wood','400','TD460',NULL,'mapped-legacy',7,'Legacy GE/Wood family.'),
 ('al-te2700','TE2700','pump','gewood-te2700','ge-wood','538','TE2700',NULL,'mapped-legacy',4,'Legacy GE/Wood family.'),
 ('al-400pmssd','400PMSSD','pump','bhce-400pm-unresolved','bhce','400',NULL,'SSD','unresolved',2,'PM construction known; hydraulic P-model not stated.'),
 ('al-400pmsnd','400PMSND','pump','bhce-400pm-unresolved','bhce','400',NULL,'SND','unresolved',1,'PM construction known; hydraulic P-model not stated.'),
 ('al-400pmshd','400PMSHD','pump','bhce-400pm-unresolved','bhce','400',NULL,'SHD','unresolved',1,'PM construction known; hydraulic P-model not stated.'),
 ('al-flexssd','FlexSSD','pump','bhce-flexssd-unresolved','bhce','400',NULL,'SSD','unresolved',1,'FLEX family known; hydraulic model missing.'),
 ('al-flex21','FLEX2.1','pump','bhce-flex21','bhce','400','FLEX2.1',NULL,'pending-verification',1,'Designation preserved as recorded.'),
 ('al-b400-750','B400-750','pump','borets-400-750','borets','400','400-750',NULL,'mapped',7,NULL);

-- Field / wells (representative CCED Block 3 sample; full 170-row load to follow)
INSERT INTO public.esp_fields (id, enterprise, name, region, block) VALUES
 ('cced-b3','CCED','CCED Block 3','Middle East','Block 3');

INSERT INTO public.esp_wells (id, field_id, pad_area, name, lift_method, well_status) VALUES
 ('W-0101','cced-b3','Area A','CCED-0101','ESP','producing'),
 ('W-0104','cced-b3','Area A','CCED-0104','ESP','producing'),
 ('W-0112','cced-b3','Area A','CCED-0112','ESP','producing'),
 ('W-0118','cced-b3','Area A','CCED-0118','ESP','producing'),
 ('W-0123','cced-b3','Area A','CCED-0123','ESP','shut-in'),
 ('W-0207','cced-b3','Area B','CCED-0207','ESP','producing'),
 ('W-0211','cced-b3','Area B','CCED-0211','ESP','producing'),
 ('W-0215','cced-b3','Area B','CCED-0215','ESP','producing'),
 ('W-0220','cced-b3','Area B','CCED-0220','ESP','producing'),
 ('W-0228','cced-b3','Area B','CCED-0228','ESP','producing'),
 ('W-0233','cced-b3','Area B','CCED-0233','ESP','producing'),
 ('W-0305','cced-b3','Area C','CCED-0305','ESP','producing'),
 ('W-0309','cced-b3','Area C','CCED-0309','ESP','producing'),
 ('W-0314','cced-b3','Area C','CCED-0314','ESP','producing'),
 ('W-0321','cced-b3','Area C','CCED-0321','ESP','producing'),
 ('W-0327','cced-b3','Area C','CCED-0327','ESP','workover'),
 ('W-0402','cced-b3','Area D','CCED-0402','ESP','producing'),
 ('W-0408','cced-b3','Area D','CCED-0408','ESP','producing'),
 ('W-0413','cced-b3','Area D','CCED-0413','ESP','producing'),
 ('W-0419','cced-b3','Area D','CCED-0419','ESP','producing'),
 ('W-0425','cced-b3','Area D','CCED-0425','ESP','producing'),
 ('W-0431','cced-b3','Area D','CCED-0431','ESP','producing'),
 ('W-0507','cced-b3','Area E','CCED-0507','ESP','producing'),
 ('W-0512','cced-b3','Area E','CCED-0512','ESP','producing');

INSERT INTO public.esp_installed_systems
 (id, well_id, raw_designation, normalized_pump_model_id, assembly_type, motor_model_id, gas_handling_model_id, protector_model_id, cable_model_id, vsd_model_id, sensor_model_id,
  total_stages, design_hz, operating_hz, install_date, run_life_days, match_confidence, match_status, unresolved_note)
VALUES
 ('IS-0101','W-0101','B400-400','borets-400-400','single','borets-m456-120','borets-gs400','borets-p400-lsbpb','borets-cbl-1awg','borets-vsd-260','borets-gauge-std',186,52,50.5,'2025-03-11',531,0.98,'matched',NULL),
 ('IS-0104','W-0104','B400-400','borets-400-400','single','borets-m456-120','borets-gs400','borets-p400-lsbpb','borets-cbl-1awg','borets-vsd-260','borets-gauge-std',210,55,54.0,'2024-11-02',660,0.98,'matched',NULL),
 ('IS-0112','W-0112','400-1050','borets-400-1050','single','borets-m456-180','borets-gh400','borets-p400-lsbpb','borets-cbl-1awg','borets-vsd-260','borets-gauge-std',142,58,57.5,'2025-06-18',432,0.97,'matched',NULL),
 ('IS-0118','W-0118','B400-1050','borets-400-1050','single','borets-m456-180','borets-gs400','borets-p400-lsbpb','borets-cbl-4awg','borets-vsd-260','borets-gauge-std',150,58,56.0,'2025-01-27',574,0.97,'matched',NULL),
 ('IS-0123','W-0123','400PMSSD','bhce-400pm-unresolved','single','bhce-m450-150','bhce-gh400','bhce-p400-bpbsl','bhce-cbl-2awg','bhce-vsd-electrospeed','bhce-centinel',NULL,NULL,NULL,'2024-08-14',740,0.35,'unresolved','PM construction family known (SSD); exact hydraulic P-model not stated in CCED record. Do not infer P4/P6/P10.'),
 ('IS-0207','W-0207','TD650','gewood-td650','single','gewood-m456-100','borets-gs400','gewood-p400-legacy','borets-cbl-4awg','gewood-vsd-legacy','borets-gauge-std',176,60,58.0,'2022-05-09',1568,0.80,'matched-legacy','Legacy GE/Wood equipment; lifecycle ownership unresolved.'),
 ('IS-0211','W-0211','B400-400','borets-400-400','single','borets-m456-120','borets-gs400','borets-p400-lsbpb','borets-cbl-1awg','borets-vsd-260','borets-gauge-std',195,52,51.0,'2025-09-30',328,0.98,'matched',NULL),
 ('IS-0215','W-0215','B400-750 + 1050','borets-400-750','composite','borets-m456-180','borets-gh400','borets-p400-lsbpb','borets-cbl-1awg','borets-vsd-260','borets-gauge-std',NULL,58,57.0,'2025-04-22',489,0.60,'partial','Composite/tapered assembly: both component hydraulics known but the total stage count is not split between sections. No composite curve until DHE/BHA stage tally is available.'),
 ('IS-0220','W-0220','400FlexER','bhce-flexpumper','single','bhce-m450-150','bhce-gh400','bhce-p400-bpbsl','bhce-cbl-2awg','bhce-vsd-electrospeed','bhce-centinel',168,55,54.5,'2025-02-15',555,0.92,'matched',NULL),
 ('IS-0228','W-0228','400-1050','borets-400-1050','single','borets-m456-180','borets-gs400','borets-p400-lsbpb','borets-cbl-1awg','borets-vsd-260','borets-gauge-std',138,58,55.0,'2024-12-05',627,0.97,'matched',NULL),
 ('IS-0233','W-0233','400-180','borets-400-180','single','borets-m456-120','borets-gs400','borets-p400-lsbpb','borets-cbl-4awg','borets-vsd-260','borets-gauge-std',260,50,48.0,'2025-07-19',401,0.96,'matched',NULL),
 ('IS-0305','W-0305','B400-400','borets-400-400','single','borets-m456-120','borets-gs400','borets-p400-lsbpb','borets-cbl-1awg','borets-vsd-260','borets-gauge-std',188,52,52.0,'2025-05-06',475,0.98,'matched',NULL),
 ('IS-0309','W-0309','TD460','gewood-td460','single','gewood-m456-100','borets-gs400','gewood-p400-legacy','borets-cbl-4awg','gewood-vsd-legacy','borets-gauge-std',204,60,57.0,'2023-03-18',1255,0.80,'matched-legacy','Legacy GE/Wood equipment.'),
 ('IS-0314','W-0314','FlexSSD','bhce-flexssd-unresolved','single','bhce-m450-150','bhce-gh400','bhce-p400-bpbsl','bhce-cbl-2awg','bhce-vsd-electrospeed','bhce-centinel',NULL,NULL,NULL,'2025-08-01',388,0.30,'unresolved','FLEX family known; exact hydraulic model missing from CCED record.'),
 ('IS-0321','W-0321','400-500','borets-400-500','single','borets-m456-120','borets-gs400','borets-p400-lsbpb','borets-cbl-1awg','borets-vsd-260','borets-gauge-std',172,55,53.5,'2025-10-11',317,0.96,'matched',NULL),
 ('IS-0327','W-0327','FLEX2.1','bhce-flex21','single','bhce-m450-150','bhce-gh400','bhce-p400-bpbsl','bhce-cbl-2awg','bhce-vsd-electrospeed','bhce-centinel',NULL,NULL,NULL,'2024-06-23',792,0.45,'pending-verification','Designation preserved; authoritative OEM verification pending.'),
 ('IS-0402','W-0402','B538-5000','borets-538-5000','single','borets-m456-180','borets-gs400','borets-p400-lsbpb','borets-cbl-1awg','borets-vsd-260','borets-gauge-std',96,58,56.5,'2025-04-03',508,0.95,'matched',NULL),
 ('IS-0408','W-0408','B538-7000','borets-538-7000','single','borets-m456-180','borets-gh400','borets-p400-lsbpb','borets-cbl-1awg','borets-vsd-260','borets-gauge-std',84,58,58.0,'2025-06-27',423,0.95,'matched',NULL),
 ('IS-0413','W-0413','B538-9000','borets-538-9000','single','borets-m456-180','borets-gh400','borets-p400-lsbpb','borets-cbl-1awg','borets-vsd-260','borets-gauge-std',72,60,59.0,'2025-09-08',350,0.95,'matched',NULL),
 ('IS-0419','W-0419','B538-3600','borets-538-3600','single','borets-m456-180','borets-gs400','borets-p400-lsbpb','borets-cbl-1awg','borets-vsd-260','borets-gauge-std',110,55,54.0,'2025-02-02',568,0.95,'matched',NULL),
 ('IS-0425','W-0425','B400-1750','borets-400-1750','single','borets-m456-180','borets-gh400','borets-p400-lsbpb','borets-cbl-1awg','borets-vsd-260','borets-gauge-std',128,58,56.0,'2025-07-30',390,0.95,'matched',NULL),
 ('IS-0431','W-0431','Flex10 SSD','bhce-flexpump10','single','bhce-m450-150','bhce-gh400','bhce-p400-bpbsl','bhce-cbl-2awg','bhce-vsd-electrospeed','bhce-centinel',NULL,55,54.0,'2025-05-21',460,0.70,'partial','FLEXPump10 SSD identified; hydraulic curve pending OEM confirmation.'),
 ('IS-0507','W-0507','TE2700','gewood-te2700','single','gewood-m456-100','borets-gs400','gewood-p400-legacy','borets-cbl-4awg','gewood-vsd-legacy','borets-gauge-std',118,60,58.5,'2022-11-14',1380,0.80,'matched-legacy','Legacy GE/Wood equipment.'),
 ('IS-0512','W-0512','B400-400','borets-400-400','single','borets-m456-120','borets-gs400','borets-p400-lsbpb','borets-cbl-1awg','borets-vsd-260','borets-gauge-std',192,52,50.0,'2026-01-19',217,0.98,'matched',NULL);

INSERT INTO public.esp_installed_pump_sections (id, installed_system_id, section_sequence, pump_model_id, raw_designation, stages, stages_known, note) VALUES
 ('PS-0101-1','IS-0101',1,'borets-400-400','B400-400',186,true,NULL),
 ('PS-0104-1','IS-0104',1,'borets-400-400','B400-400',210,true,NULL),
 ('PS-0112-1','IS-0112',1,'borets-400-1050','400-1050',142,true,NULL),
 ('PS-0118-1','IS-0118',1,'borets-400-1050','B400-1050',150,true,NULL),
 ('PS-0123-1','IS-0123',1,'bhce-400pm-unresolved','400PMSSD',NULL,false,'Hydraulic model unresolved; stage count not usable for calculation.'),
 ('PS-0215-1','IS-0215',1,'borets-400-750','B400-750',NULL,false,'Lower section — stage split not recorded in CCED workbook.'),
 ('PS-0215-2','IS-0215',2,'borets-400-1050','1050',NULL,false,'Upper section — stage split not recorded in CCED workbook.'),
 ('PS-0220-1','IS-0220',1,'bhce-flexpumper','400FlexER',168,true,NULL),
 ('PS-0402-1','IS-0402',1,'borets-538-5000','B538-5000',96,true,NULL),
 ('PS-0408-1','IS-0408',1,'borets-538-7000','B538-7000',84,true,NULL),
 ('PS-0413-1','IS-0413',1,'borets-538-9000','B538-9000',72,true,NULL),
 ('PS-0419-1','IS-0419',1,'borets-538-3600','B538-3600',110,true,NULL),
 ('PS-0425-1','IS-0425',1,'borets-400-1750','B400-1750',128,true,NULL);

INSERT INTO public.esp_well_engineering (well_id, casing_od_in, casing_weight_lb_ft, tubing_id_in, pump_setting_depth_ft, perf_top_ft, perf_bottom_ft, deviation_at_pump_deg, reservoir_pressure_psi, productivity_index_bpd_psi, bht_f, source_id, reliability_code) VALUES
 ('W-0101',7.0,26,2.441,6420,7100,7260,18,2850,0.62,196,'src-cced-wb','A2'),
 ('W-0112',7.0,26,2.441,6810,7400,7580,22,2960,1.10,201,'src-cced-wb','A2'),
 ('W-0207',7.0,29,2.441,6150,6800,6950,12,2740,0.74,188,'src-cced-wb','B2'),
 ('W-0402',9.625,47,3.548,7320,7900,8140,9,3410,2.35,214,'src-cced-wb','A2'),
 ('W-0215',7.0,26,2.441,6980,7550,7720,26,3020,1.05,205,'src-cced-wb','A2');

INSERT INTO public.esp_fluid_pvt (well_id, oil_api, water_sg, gas_sg, water_cut_pct, gor_scf_stb, bubble_point_psi, viscosity_cp, h2s_ppm, co2_pct, sample_date, source_id, reliability_code) VALUES
 ('W-0101',31.5,1.06,0.72,68,340,1850,2.1,15,1.4,'2025-11-04','src-cced-wb','A2'),
 ('W-0112',30.8,1.07,0.74,74,410,1920,2.4,22,1.6,'2025-10-18','src-cced-wb','A2'),
 ('W-0207',29.6,1.05,0.71,81,290,1760,2.9,9,1.2,'2024-09-12','src-cced-wb','B2'),
 ('W-0402',33.2,1.06,0.70,56,520,2050,1.8,31,1.9,'2026-01-22','src-cced-wb','A2'),
 ('W-0215',30.1,1.07,0.73,77,455,1980,2.5,18,1.5,'2025-12-09','src-cced-wb','A2');

INSERT INTO public.esp_design_limits (well_id, min_hz, max_hz, min_pip_psi, max_motor_temp_f, max_motor_load_pct, max_vibration_g, ror_min_bpd, ror_max_bpd, envelope_basis, source_id, reliability_code) VALUES
 ('W-0101',45,58,320,415,95,0.40,250,600,'OEM catalog ROR at installed frequency','src-borets-cat','A2'),
 ('W-0112',48,60,350,415,95,0.40,700,1400,'OEM catalog ROR at installed frequency','src-borets-cat','A2'),
 ('W-0207',45,60,300,380,90,0.35,400,900,'Legacy catalog envelope — verification pending','src-ge-wood-cat','B2'),
 ('W-0402',48,60,420,415,95,0.40,1509,6350,'Borets historical compression ROR (WSW cross-check MATCH)','src-borets-comp','B2'),
 ('W-0215',48,60,360,415,95,0.40,NULL,NULL,'Composite assembly — envelope blocked until stage split is known','src-unresolved','D');

INSERT INTO public.esp_data_quality_issues (id, title, category, severity, status, scope, raw_designation, pump_model_id, affected_installations, detail, required_action, owner, opened_at) VALUES
 ('DQ-001','400PM construction family without hydraulic model','model-identity','Blocking','Open','Equipment Catalog · Pump Models','400PMSSD / 400PMSND / 400PMSHD','bhce-400pm-unresolved',4,'PM construction family (SSD/SND/SHD) is recorded but the exact hydraulic P-model is not stated in the CCED workbook. P4/P6/P10 must not be inferred.','Request OEM confirmation of the hydraulic P-model per installation before any curve-based calculation.','Catalog Engineering','2026-08-15'),
 ('DQ-002','FlexSSD installation without hydraulic model','model-identity','Blocking','Open','Installed Fleet','FlexSSD','bhce-flexssd-unresolved',1,'FLEX family and SSD construction known; exact hydraulic model missing.','Obtain DHE record or OEM installation report to resolve the hydraulic model.','Catalog Engineering','2026-08-15'),
 ('DQ-003','FLEX2.1 designation pending OEM verification','verification','Open','Open','Equipment Catalog · Pump Models','FLEX2.1','bhce-flex21',1,'Designation preserved exactly as recorded. Currently C1 (secondary/discovery) evidence only.','Raise OEM verification request; do not promote to calculation grade until A1/A2 evidence exists.','Catalog Engineering','2026-08-16'),
 ('DQ-004','Composite B400-750 + 1050 stage split unknown','assembly-completeness','Blocking','Open','Installed Fleet','B400-750 + 1050','borets-400-750',1,'Both component hydraulic models are known, but the total stage count is not split between the two pump sections.','Retrieve DHE/BHA stage tally, then populate both pump sections. No composite curve until then.','Well Engineering','2026-08-17'),
 ('DQ-005','Legacy TD/TE lifecycle ownership unresolved','governance','Governance','Open','Equipment Catalog · Pump Models',NULL,'gewood-td650',24,'Legacy GE Oil & Gas / Wood Group equipment: current support ownership and lifecycle status remain historical/unresolved.','Confirm current support ownership with the customer supply-chain team; keep lifecycle flagged historical until verified.','Reliability','2026-07-02'),
 ('DQ-006','Pengtools-only identifications must not be promoted','governance','Governance','Open','Source Registry',NULL,NULL,0,'Pengtools is a curated secondary catalog (C1). It may identify a model but must never be promoted to calculation-grade data automatically.','Keep C1 sources discovery-only; require A1/A2 evidence before enabling curve-based calculation.','Data Governance','2026-06-11'),
 ('DQ-007','WSW design-capacity ranges cross-checked against Borets compression ROR','validation','Resolved','Resolved','Engineering Validation',NULL,NULL,17,'B538-3600, B538-5000, B538-7000, B538-9000 and B400-1750 customer WSW design-capacity ranges independently reconciled against Borets historical compression ROR data — all MATCH.','No action; retain as traceability evidence.','Catalog Engineering','2026-08-02'),
 ('DQ-008','Curve digitisation pending for high-count Series 400 hydraulics','curve-coverage','Open','Open','Equipment Catalog · Pump Curves',NULL,'borets-400-180',28,'400-180, 400-500, 400-750 and FLEXPumpER currently hold BEP/envelope evidence only; no digitised curve points exist.','Digitise catalog curves from licensed OEM source, or mark permanently as BEP/Envelope only.','Catalog Engineering','2026-08-18');