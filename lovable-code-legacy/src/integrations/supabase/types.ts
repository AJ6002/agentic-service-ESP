export type Json =
  | string
  | number
  | boolean
  | null
  | { [key: string]: Json | undefined }
  | Json[]

export type Database = {
  // Allows to automatically instantiate createClient with right options
  // instead of createClient<Database, { PostgrestVersion: 'XX' }>(URL, KEY)
  __InternalSupabase: {
    PostgrestVersion: "14.15"
  }
  public: {
    Tables: {
      esp_cable_models: {
        Row: {
          armor: string | null
          cable_type: string | null
          cced_installed_count: number
          conductor_size_awg: string | null
          created_at: string
          id: string
          max_temp_f: number | null
          model: string
          oem_id: string
          reliability_code: string
          resistance_ohm_per_kft: number | null
          source_id: string | null
          updated_at: string
          verification_status: string
          voltage_rating_v: number | null
        }
        Insert: {
          armor?: string | null
          cable_type?: string | null
          cced_installed_count?: number
          conductor_size_awg?: string | null
          created_at?: string
          id: string
          max_temp_f?: number | null
          model: string
          oem_id: string
          reliability_code?: string
          resistance_ohm_per_kft?: number | null
          source_id?: string | null
          updated_at?: string
          verification_status?: string
          voltage_rating_v?: number | null
        }
        Update: {
          armor?: string | null
          cable_type?: string | null
          cced_installed_count?: number
          conductor_size_awg?: string | null
          created_at?: string
          id?: string
          max_temp_f?: number | null
          model?: string
          oem_id?: string
          reliability_code?: string
          resistance_ohm_per_kft?: number | null
          source_id?: string | null
          updated_at?: string
          verification_status?: string
          voltage_rating_v?: number | null
        }
        Relationships: [
          {
            foreignKeyName: "esp_cable_models_oem_id_fkey"
            columns: ["oem_id"]
            isOneToOne: false
            referencedRelation: "esp_oems"
            referencedColumns: ["id"]
          },
          {
            foreignKeyName: "esp_cable_models_source_id_fkey"
            columns: ["source_id"]
            isOneToOne: false
            referencedRelation: "esp_sources"
            referencedColumns: ["id"]
          },
        ]
      }
      esp_catalog_aliases: {
        Row: {
          cced_occurrences: number
          construction_variant: string | null
          created_at: string
          entity_kind: string
          id: string
          mapping_status: string
          normalized_model: string | null
          normalized_oem_id: string | null
          normalized_series: string | null
          note: string | null
          pump_model_id: string | null
          raw_designation: string
          source_id: string | null
          updated_at: string
        }
        Insert: {
          cced_occurrences?: number
          construction_variant?: string | null
          created_at?: string
          entity_kind?: string
          id: string
          mapping_status?: string
          normalized_model?: string | null
          normalized_oem_id?: string | null
          normalized_series?: string | null
          note?: string | null
          pump_model_id?: string | null
          raw_designation: string
          source_id?: string | null
          updated_at?: string
        }
        Update: {
          cced_occurrences?: number
          construction_variant?: string | null
          created_at?: string
          entity_kind?: string
          id?: string
          mapping_status?: string
          normalized_model?: string | null
          normalized_oem_id?: string | null
          normalized_series?: string | null
          note?: string | null
          pump_model_id?: string | null
          raw_designation?: string
          source_id?: string | null
          updated_at?: string
        }
        Relationships: [
          {
            foreignKeyName: "esp_catalog_aliases_normalized_oem_id_fkey"
            columns: ["normalized_oem_id"]
            isOneToOne: false
            referencedRelation: "esp_oems"
            referencedColumns: ["id"]
          },
          {
            foreignKeyName: "esp_catalog_aliases_pump_model_id_fkey"
            columns: ["pump_model_id"]
            isOneToOne: false
            referencedRelation: "esp_pump_models"
            referencedColumns: ["id"]
          },
          {
            foreignKeyName: "esp_catalog_aliases_source_id_fkey"
            columns: ["source_id"]
            isOneToOne: false
            referencedRelation: "esp_sources"
            referencedColumns: ["id"]
          },
        ]
      }
      esp_catalog_discovery: {
        Row: {
          brand_raw: string | null
          created_at: string | null
          engineering_use: string | null
          id: number
          manufacturer_raw: string | null
          model_raw: string | null
          normalized_model: string | null
          oem_verification: string | null
          performance_curve_status: string | null
          qa_flag: string | null
          reliability_code: string | null
          series_raw: string | null
          source_id: string | null
          source_reported_total: number | null
        }
        Insert: {
          brand_raw?: string | null
          created_at?: string | null
          engineering_use?: string | null
          id?: number
          manufacturer_raw?: string | null
          model_raw?: string | null
          normalized_model?: string | null
          oem_verification?: string | null
          performance_curve_status?: string | null
          qa_flag?: string | null
          reliability_code?: string | null
          series_raw?: string | null
          source_id?: string | null
          source_reported_total?: number | null
        }
        Update: {
          brand_raw?: string | null
          created_at?: string | null
          engineering_use?: string | null
          id?: number
          manufacturer_raw?: string | null
          model_raw?: string | null
          normalized_model?: string | null
          oem_verification?: string | null
          performance_curve_status?: string | null
          qa_flag?: string | null
          reliability_code?: string | null
          series_raw?: string | null
          source_id?: string | null
          source_reported_total?: number | null
        }
        Relationships: [
          {
            foreignKeyName: "esp_catalog_discovery_source_id_fkey"
            columns: ["source_id"]
            isOneToOne: false
            referencedRelation: "esp_sources"
            referencedColumns: ["id"]
          },
        ]
      }
      esp_data_quality_issues: {
        Row: {
          affected_installations: number
          category: string
          created_at: string
          detail: string | null
          id: string
          opened_at: string | null
          owner: string | null
          pump_model_id: string | null
          raw_designation: string | null
          required_action: string | null
          scope: string | null
          severity: string
          status: string
          title: string
          updated_at: string
        }
        Insert: {
          affected_installations?: number
          category: string
          created_at?: string
          detail?: string | null
          id: string
          opened_at?: string | null
          owner?: string | null
          pump_model_id?: string | null
          raw_designation?: string | null
          required_action?: string | null
          scope?: string | null
          severity?: string
          status?: string
          title: string
          updated_at?: string
        }
        Update: {
          affected_installations?: number
          category?: string
          created_at?: string
          detail?: string | null
          id?: string
          opened_at?: string | null
          owner?: string | null
          pump_model_id?: string | null
          raw_designation?: string | null
          required_action?: string | null
          scope?: string | null
          severity?: string
          status?: string
          title?: string
          updated_at?: string
        }
        Relationships: [
          {
            foreignKeyName: "esp_data_quality_issues_pump_model_id_fkey"
            columns: ["pump_model_id"]
            isOneToOne: false
            referencedRelation: "esp_pump_models"
            referencedColumns: ["id"]
          },
        ]
      }
      esp_design_limits: {
        Row: {
          created_at: string
          envelope_basis: string | null
          max_hz: number | null
          max_motor_load_pct: number | null
          max_motor_temp_f: number | null
          max_vibration_g: number | null
          min_hz: number | null
          min_pip_psi: number | null
          reliability_code: string
          ror_max_bpd: number | null
          ror_min_bpd: number | null
          source_id: string | null
          updated_at: string
          well_id: string
        }
        Insert: {
          created_at?: string
          envelope_basis?: string | null
          max_hz?: number | null
          max_motor_load_pct?: number | null
          max_motor_temp_f?: number | null
          max_vibration_g?: number | null
          min_hz?: number | null
          min_pip_psi?: number | null
          reliability_code?: string
          ror_max_bpd?: number | null
          ror_min_bpd?: number | null
          source_id?: string | null
          updated_at?: string
          well_id: string
        }
        Update: {
          created_at?: string
          envelope_basis?: string | null
          max_hz?: number | null
          max_motor_load_pct?: number | null
          max_motor_temp_f?: number | null
          max_vibration_g?: number | null
          min_hz?: number | null
          min_pip_psi?: number | null
          reliability_code?: string
          ror_max_bpd?: number | null
          ror_min_bpd?: number | null
          source_id?: string | null
          updated_at?: string
          well_id?: string
        }
        Relationships: [
          {
            foreignKeyName: "esp_design_limits_source_id_fkey"
            columns: ["source_id"]
            isOneToOne: false
            referencedRelation: "esp_sources"
            referencedColumns: ["id"]
          },
          {
            foreignKeyName: "esp_design_limits_well_id_fkey"
            columns: ["well_id"]
            isOneToOne: true
            referencedRelation: "esp_wells"
            referencedColumns: ["id"]
          },
        ]
      }
      esp_engineering_validations: {
        Row: {
          catalog_ror_max_bpd: number | null
          catalog_ror_min_bpd: number | null
          created_at: string | null
          customer_capacity_range: string | null
          id: string
          normalized_model: string | null
          normalized_oem: string | null
          notes: string | null
          pump_type_raw: string | null
          range_verification: string | null
          series: string | null
          source_id: string | null
          well_id: string | null
        }
        Insert: {
          catalog_ror_max_bpd?: number | null
          catalog_ror_min_bpd?: number | null
          created_at?: string | null
          customer_capacity_range?: string | null
          id: string
          normalized_model?: string | null
          normalized_oem?: string | null
          notes?: string | null
          pump_type_raw?: string | null
          range_verification?: string | null
          series?: string | null
          source_id?: string | null
          well_id?: string | null
        }
        Update: {
          catalog_ror_max_bpd?: number | null
          catalog_ror_min_bpd?: number | null
          created_at?: string | null
          customer_capacity_range?: string | null
          id?: string
          normalized_model?: string | null
          normalized_oem?: string | null
          notes?: string | null
          pump_type_raw?: string | null
          range_verification?: string | null
          series?: string | null
          source_id?: string | null
          well_id?: string | null
        }
        Relationships: [
          {
            foreignKeyName: "esp_engineering_validations_source_id_fkey"
            columns: ["source_id"]
            isOneToOne: false
            referencedRelation: "esp_sources"
            referencedColumns: ["id"]
          },
        ]
      }
      esp_fields: {
        Row: {
          block: string | null
          created_at: string
          enterprise: string
          id: string
          name: string
          region: string | null
          updated_at: string
        }
        Insert: {
          block?: string | null
          created_at?: string
          enterprise: string
          id: string
          name: string
          region?: string | null
          updated_at?: string
        }
        Update: {
          block?: string | null
          created_at?: string
          enterprise?: string
          id?: string
          name?: string
          region?: string | null
          updated_at?: string
        }
        Relationships: []
      }
      esp_fluid_pvt: {
        Row: {
          bubble_point_psi: number | null
          co2_pct: number | null
          created_at: string
          gas_sg: number | null
          gor_scf_stb: number | null
          h2s_ppm: number | null
          oil_api: number | null
          reliability_code: string
          sample_date: string | null
          source_id: string | null
          updated_at: string
          viscosity_cp: number | null
          water_cut_pct: number | null
          water_sg: number | null
          well_id: string
        }
        Insert: {
          bubble_point_psi?: number | null
          co2_pct?: number | null
          created_at?: string
          gas_sg?: number | null
          gor_scf_stb?: number | null
          h2s_ppm?: number | null
          oil_api?: number | null
          reliability_code?: string
          sample_date?: string | null
          source_id?: string | null
          updated_at?: string
          viscosity_cp?: number | null
          water_cut_pct?: number | null
          water_sg?: number | null
          well_id: string
        }
        Update: {
          bubble_point_psi?: number | null
          co2_pct?: number | null
          created_at?: string
          gas_sg?: number | null
          gor_scf_stb?: number | null
          h2s_ppm?: number | null
          oil_api?: number | null
          reliability_code?: string
          sample_date?: string | null
          source_id?: string | null
          updated_at?: string
          viscosity_cp?: number | null
          water_cut_pct?: number | null
          water_sg?: number | null
          well_id?: string
        }
        Relationships: [
          {
            foreignKeyName: "esp_fluid_pvt_source_id_fkey"
            columns: ["source_id"]
            isOneToOne: false
            referencedRelation: "esp_sources"
            referencedColumns: ["id"]
          },
          {
            foreignKeyName: "esp_fluid_pvt_well_id_fkey"
            columns: ["well_id"]
            isOneToOne: true
            referencedRelation: "esp_wells"
            referencedColumns: ["id"]
          },
        ]
      }
      esp_gas_handling_models: {
        Row: {
          cced_installed_count: number
          created_at: string
          device_type: string
          id: string
          max_flow_bpd: number | null
          max_gvf_pct: number | null
          min_flow_bpd: number | null
          model: string
          notes: string | null
          od_in: number | null
          oem_id: string
          reliability_code: string
          separation_eff_max_pct: number | null
          series: string | null
          source_id: string | null
          updated_at: string
          verification_status: string
        }
        Insert: {
          cced_installed_count?: number
          created_at?: string
          device_type: string
          id: string
          max_flow_bpd?: number | null
          max_gvf_pct?: number | null
          min_flow_bpd?: number | null
          model: string
          notes?: string | null
          od_in?: number | null
          oem_id: string
          reliability_code?: string
          separation_eff_max_pct?: number | null
          series?: string | null
          source_id?: string | null
          updated_at?: string
          verification_status?: string
        }
        Update: {
          cced_installed_count?: number
          created_at?: string
          device_type?: string
          id?: string
          max_flow_bpd?: number | null
          max_gvf_pct?: number | null
          min_flow_bpd?: number | null
          model?: string
          notes?: string | null
          od_in?: number | null
          oem_id?: string
          reliability_code?: string
          separation_eff_max_pct?: number | null
          series?: string | null
          source_id?: string | null
          updated_at?: string
          verification_status?: string
        }
        Relationships: [
          {
            foreignKeyName: "esp_gas_handling_models_oem_id_fkey"
            columns: ["oem_id"]
            isOneToOne: false
            referencedRelation: "esp_oems"
            referencedColumns: ["id"]
          },
          {
            foreignKeyName: "esp_gas_handling_models_source_id_fkey"
            columns: ["source_id"]
            isOneToOne: false
            referencedRelation: "esp_sources"
            referencedColumns: ["id"]
          },
        ]
      }
      esp_installed_pump_sections: {
        Row: {
          created_at: string
          id: string
          installed_system_id: string
          note: string | null
          pump_model_id: string | null
          raw_designation: string | null
          section_sequence: number
          stages: number | null
          stages_known: boolean
        }
        Insert: {
          created_at?: string
          id: string
          installed_system_id: string
          note?: string | null
          pump_model_id?: string | null
          raw_designation?: string | null
          section_sequence: number
          stages?: number | null
          stages_known?: boolean
        }
        Update: {
          created_at?: string
          id?: string
          installed_system_id?: string
          note?: string | null
          pump_model_id?: string | null
          raw_designation?: string | null
          section_sequence?: number
          stages?: number | null
          stages_known?: boolean
        }
        Relationships: [
          {
            foreignKeyName: "esp_installed_pump_sections_installed_system_id_fkey"
            columns: ["installed_system_id"]
            isOneToOne: false
            referencedRelation: "esp_installed_systems"
            referencedColumns: ["id"]
          },
          {
            foreignKeyName: "esp_installed_pump_sections_pump_model_id_fkey"
            columns: ["pump_model_id"]
            isOneToOne: false
            referencedRelation: "esp_pump_models"
            referencedColumns: ["id"]
          },
        ]
      }
      esp_installed_systems: {
        Row: {
          assembly_type: string
          brand_line: string | null
          cable_model_id: string | null
          cluster: string | null
          comments: string | null
          connection_raw: string | null
          construction_or_suffix: string | null
          created_at: string
          design_hz: number | null
          gas_handling_model_id: string | null
          id: string
          install_date: string | null
          library_match_id: string | null
          match_confidence: number | null
          match_confidence_text: string | null
          match_status: string
          motor_amp_50hz: number | null
          motor_hp_50hz: number | null
          motor_model_id: string | null
          motor_volt_50hz: number | null
          normalized_model: string | null
          normalized_oem: string | null
          normalized_pump_model_id: string | null
          operating_hz: number | null
          protector_model_id: string | null
          qa_flag: string | null
          raw_designation: string | null
          reliability_code: string | null
          run_life_days: number | null
          sensor_model_id: string | null
          series: string | null
          source_id: string | null
          stepup_xfmr: string | null
          tap_range: string | null
          tap_selector: string | null
          total_stages: number | null
          unresolved_note: string | null
          updated_at: string
          volt_at_tap: string | null
          vsd_kva_or_rating: string | null
          vsd_manufacturer_raw: string | null
          vsd_model_id: string | null
          vsd_model_raw: string | null
          vsd_skid: string | null
          vsd_sn: string | null
          well_id: string
          xfmr_manufacturer: string | null
          xfmr_sn: string | null
        }
        Insert: {
          assembly_type?: string
          brand_line?: string | null
          cable_model_id?: string | null
          cluster?: string | null
          comments?: string | null
          connection_raw?: string | null
          construction_or_suffix?: string | null
          created_at?: string
          design_hz?: number | null
          gas_handling_model_id?: string | null
          id: string
          install_date?: string | null
          library_match_id?: string | null
          match_confidence?: number | null
          match_confidence_text?: string | null
          match_status?: string
          motor_amp_50hz?: number | null
          motor_hp_50hz?: number | null
          motor_model_id?: string | null
          motor_volt_50hz?: number | null
          normalized_model?: string | null
          normalized_oem?: string | null
          normalized_pump_model_id?: string | null
          operating_hz?: number | null
          protector_model_id?: string | null
          qa_flag?: string | null
          raw_designation?: string | null
          reliability_code?: string | null
          run_life_days?: number | null
          sensor_model_id?: string | null
          series?: string | null
          source_id?: string | null
          stepup_xfmr?: string | null
          tap_range?: string | null
          tap_selector?: string | null
          total_stages?: number | null
          unresolved_note?: string | null
          updated_at?: string
          volt_at_tap?: string | null
          vsd_kva_or_rating?: string | null
          vsd_manufacturer_raw?: string | null
          vsd_model_id?: string | null
          vsd_model_raw?: string | null
          vsd_skid?: string | null
          vsd_sn?: string | null
          well_id: string
          xfmr_manufacturer?: string | null
          xfmr_sn?: string | null
        }
        Update: {
          assembly_type?: string
          brand_line?: string | null
          cable_model_id?: string | null
          cluster?: string | null
          comments?: string | null
          connection_raw?: string | null
          construction_or_suffix?: string | null
          created_at?: string
          design_hz?: number | null
          gas_handling_model_id?: string | null
          id?: string
          install_date?: string | null
          library_match_id?: string | null
          match_confidence?: number | null
          match_confidence_text?: string | null
          match_status?: string
          motor_amp_50hz?: number | null
          motor_hp_50hz?: number | null
          motor_model_id?: string | null
          motor_volt_50hz?: number | null
          normalized_model?: string | null
          normalized_oem?: string | null
          normalized_pump_model_id?: string | null
          operating_hz?: number | null
          protector_model_id?: string | null
          qa_flag?: string | null
          raw_designation?: string | null
          reliability_code?: string | null
          run_life_days?: number | null
          sensor_model_id?: string | null
          series?: string | null
          source_id?: string | null
          stepup_xfmr?: string | null
          tap_range?: string | null
          tap_selector?: string | null
          total_stages?: number | null
          unresolved_note?: string | null
          updated_at?: string
          volt_at_tap?: string | null
          vsd_kva_or_rating?: string | null
          vsd_manufacturer_raw?: string | null
          vsd_model_id?: string | null
          vsd_model_raw?: string | null
          vsd_skid?: string | null
          vsd_sn?: string | null
          well_id?: string
          xfmr_manufacturer?: string | null
          xfmr_sn?: string | null
        }
        Relationships: [
          {
            foreignKeyName: "esp_installed_systems_cable_model_id_fkey"
            columns: ["cable_model_id"]
            isOneToOne: false
            referencedRelation: "esp_cable_models"
            referencedColumns: ["id"]
          },
          {
            foreignKeyName: "esp_installed_systems_gas_handling_model_id_fkey"
            columns: ["gas_handling_model_id"]
            isOneToOne: false
            referencedRelation: "esp_gas_handling_models"
            referencedColumns: ["id"]
          },
          {
            foreignKeyName: "esp_installed_systems_motor_model_id_fkey"
            columns: ["motor_model_id"]
            isOneToOne: false
            referencedRelation: "esp_motor_models"
            referencedColumns: ["id"]
          },
          {
            foreignKeyName: "esp_installed_systems_normalized_pump_model_id_fkey"
            columns: ["normalized_pump_model_id"]
            isOneToOne: false
            referencedRelation: "esp_pump_models"
            referencedColumns: ["id"]
          },
          {
            foreignKeyName: "esp_installed_systems_protector_model_id_fkey"
            columns: ["protector_model_id"]
            isOneToOne: false
            referencedRelation: "esp_protector_models"
            referencedColumns: ["id"]
          },
          {
            foreignKeyName: "esp_installed_systems_sensor_model_id_fkey"
            columns: ["sensor_model_id"]
            isOneToOne: false
            referencedRelation: "esp_sensor_models"
            referencedColumns: ["id"]
          },
          {
            foreignKeyName: "esp_installed_systems_source_id_fkey"
            columns: ["source_id"]
            isOneToOne: false
            referencedRelation: "esp_sources"
            referencedColumns: ["id"]
          },
          {
            foreignKeyName: "esp_installed_systems_vsd_model_id_fkey"
            columns: ["vsd_model_id"]
            isOneToOne: false
            referencedRelation: "esp_vsd_models"
            referencedColumns: ["id"]
          },
          {
            foreignKeyName: "esp_installed_systems_well_id_fkey"
            columns: ["well_id"]
            isOneToOne: false
            referencedRelation: "esp_wells"
            referencedColumns: ["id"]
          },
        ]
      }
      esp_motor_models: {
        Row: {
          brand_line: string | null
          cced_installed_count: number
          configuration_notes: string | null
          construction_note: string | null
          created_at: string
          hp_max: number | null
          hp_min: number | null
          id: string
          max_temp_f: number | null
          max_winding_temp_c: number | null
          model: string
          nameplate_amps: number | null
          nameplate_hp: number | null
          nameplate_volts: number | null
          od_in: number | null
          oem_id: string
          reliability_code: string
          series: string | null
          source_id: string | null
          updated_at: string
          verification_status: string
          winding_type: string | null
        }
        Insert: {
          brand_line?: string | null
          cced_installed_count?: number
          configuration_notes?: string | null
          construction_note?: string | null
          created_at?: string
          hp_max?: number | null
          hp_min?: number | null
          id: string
          max_temp_f?: number | null
          max_winding_temp_c?: number | null
          model: string
          nameplate_amps?: number | null
          nameplate_hp?: number | null
          nameplate_volts?: number | null
          od_in?: number | null
          oem_id: string
          reliability_code?: string
          series?: string | null
          source_id?: string | null
          updated_at?: string
          verification_status?: string
          winding_type?: string | null
        }
        Update: {
          brand_line?: string | null
          cced_installed_count?: number
          configuration_notes?: string | null
          construction_note?: string | null
          created_at?: string
          hp_max?: number | null
          hp_min?: number | null
          id?: string
          max_temp_f?: number | null
          max_winding_temp_c?: number | null
          model?: string
          nameplate_amps?: number | null
          nameplate_hp?: number | null
          nameplate_volts?: number | null
          od_in?: number | null
          oem_id?: string
          reliability_code?: string
          series?: string | null
          source_id?: string | null
          updated_at?: string
          verification_status?: string
          winding_type?: string | null
        }
        Relationships: [
          {
            foreignKeyName: "esp_motor_models_oem_id_fkey"
            columns: ["oem_id"]
            isOneToOne: false
            referencedRelation: "esp_oems"
            referencedColumns: ["id"]
          },
          {
            foreignKeyName: "esp_motor_models_source_id_fkey"
            columns: ["source_id"]
            isOneToOne: false
            referencedRelation: "esp_sources"
            referencedColumns: ["id"]
          },
        ]
      }
      esp_oems: {
        Row: {
          created_at: string
          id: string
          legal_note: string | null
          lifecycle_status: string
          name: string
          updated_at: string
        }
        Insert: {
          created_at?: string
          id: string
          legal_note?: string | null
          lifecycle_status?: string
          name: string
          updated_at?: string
        }
        Update: {
          created_at?: string
          id?: string
          legal_note?: string | null
          lifecycle_status?: string
          name?: string
          updated_at?: string
        }
        Relationships: []
      }
      esp_protector_models: {
        Row: {
          cced_installed_count: number
          chamber_count: number | null
          configuration: string | null
          created_at: string
          elastomer: string | null
          id: string
          model: string
          od_in: number | null
          oem_id: string
          reliability_code: string
          source_id: string | null
          thrust_bearing_rating_lbf: number | null
          updated_at: string
          verification_status: string
        }
        Insert: {
          cced_installed_count?: number
          chamber_count?: number | null
          configuration?: string | null
          created_at?: string
          elastomer?: string | null
          id: string
          model: string
          od_in?: number | null
          oem_id: string
          reliability_code?: string
          source_id?: string | null
          thrust_bearing_rating_lbf?: number | null
          updated_at?: string
          verification_status?: string
        }
        Update: {
          cced_installed_count?: number
          chamber_count?: number | null
          configuration?: string | null
          created_at?: string
          elastomer?: string | null
          id?: string
          model?: string
          od_in?: number | null
          oem_id?: string
          reliability_code?: string
          source_id?: string | null
          thrust_bearing_rating_lbf?: number | null
          updated_at?: string
          verification_status?: string
        }
        Relationships: [
          {
            foreignKeyName: "esp_protector_models_oem_id_fkey"
            columns: ["oem_id"]
            isOneToOne: false
            referencedRelation: "esp_oems"
            referencedColumns: ["id"]
          },
          {
            foreignKeyName: "esp_protector_models_source_id_fkey"
            columns: ["source_id"]
            isOneToOne: false
            referencedRelation: "esp_sources"
            referencedColumns: ["id"]
          },
        ]
      }
      esp_pump_curve_points: {
        Row: {
          confidence: number | null
          created_at: string
          curve_revision: string
          efficiency_pct: number | null
          extraction_method: string | null
          flow_bpd: number
          head_ft_per_stage: number | null
          id: number
          point_sequence: number
          power_hp_per_stage: number | null
          pump_model_id: string
          reference_hz: number
          reference_rpm: number | null
          source_id: string | null
          stage_basis: string
        }
        Insert: {
          confidence?: number | null
          created_at?: string
          curve_revision?: string
          efficiency_pct?: number | null
          extraction_method?: string | null
          flow_bpd: number
          head_ft_per_stage?: number | null
          id?: number
          point_sequence: number
          power_hp_per_stage?: number | null
          pump_model_id: string
          reference_hz: number
          reference_rpm?: number | null
          source_id?: string | null
          stage_basis?: string
        }
        Update: {
          confidence?: number | null
          created_at?: string
          curve_revision?: string
          efficiency_pct?: number | null
          extraction_method?: string | null
          flow_bpd?: number
          head_ft_per_stage?: number | null
          id?: number
          point_sequence?: number
          power_hp_per_stage?: number | null
          pump_model_id?: string
          reference_hz?: number
          reference_rpm?: number | null
          source_id?: string | null
          stage_basis?: string
        }
        Relationships: [
          {
            foreignKeyName: "esp_pump_curve_points_pump_model_id_fkey"
            columns: ["pump_model_id"]
            isOneToOne: false
            referencedRelation: "esp_pump_models"
            referencedColumns: ["id"]
          },
          {
            foreignKeyName: "esp_pump_curve_points_source_id_fkey"
            columns: ["source_id"]
            isOneToOne: false
            referencedRelation: "esp_sources"
            referencedColumns: ["id"]
          },
        ]
      }
      esp_pump_models: {
        Row: {
          application_note: string | null
          bearing_material: string | null
          bep_efficiency_pct: number | null
          bep_flow_bpd: number | null
          bep_head_ft_per_stage: number | null
          bep_power_hp_per_stage: number | null
          brand_line: string | null
          cced_installed_count: number
          cced_installed_wells: string | null
          cced_motor_hp_max: number | null
          cced_motor_hp_min: number | null
          cced_raw_aliases: string | null
          cced_stage_max: number | null
          cced_stage_min: number | null
          compression_ror_max_bpd: number | null
          compression_ror_min_bpd: number | null
          construction_type: string | null
          created_at: string
          curve_completeness: string
          floater_ror_max_bpd: number | null
          floater_ror_min_bpd: number | null
          housing_burst_psi: number | null
          id: string
          last_review_date: string | null
          lifecycle_status: string
          min_casing_in: number | null
          model: string
          model_revision: string | null
          notes: string | null
          od_in: number | null
          oem_id: string
          reference_hz: number | null
          reference_rpm: number | null
          reliability_code: string
          ror_max_bpd: number | null
          ror_min_bpd: number | null
          series: string | null
          shaft_diameter_in: number | null
          shaft_hp_high_strength: number | null
          shaft_hp_limit: number | null
          shaft_material: string | null
          source_id: string | null
          stage_geometry: string | null
          stage_material: string | null
          temperature_note: string | null
          updated_at: string
          usage_rights_status: string
          verification_status: string
          wsw_crosscheck_result: string | null
          wsw_design_max_bpd: number | null
          wsw_design_min_bpd: number | null
        }
        Insert: {
          application_note?: string | null
          bearing_material?: string | null
          bep_efficiency_pct?: number | null
          bep_flow_bpd?: number | null
          bep_head_ft_per_stage?: number | null
          bep_power_hp_per_stage?: number | null
          brand_line?: string | null
          cced_installed_count?: number
          cced_installed_wells?: string | null
          cced_motor_hp_max?: number | null
          cced_motor_hp_min?: number | null
          cced_raw_aliases?: string | null
          cced_stage_max?: number | null
          cced_stage_min?: number | null
          compression_ror_max_bpd?: number | null
          compression_ror_min_bpd?: number | null
          construction_type?: string | null
          created_at?: string
          curve_completeness?: string
          floater_ror_max_bpd?: number | null
          floater_ror_min_bpd?: number | null
          housing_burst_psi?: number | null
          id: string
          last_review_date?: string | null
          lifecycle_status?: string
          min_casing_in?: number | null
          model: string
          model_revision?: string | null
          notes?: string | null
          od_in?: number | null
          oem_id: string
          reference_hz?: number | null
          reference_rpm?: number | null
          reliability_code?: string
          ror_max_bpd?: number | null
          ror_min_bpd?: number | null
          series?: string | null
          shaft_diameter_in?: number | null
          shaft_hp_high_strength?: number | null
          shaft_hp_limit?: number | null
          shaft_material?: string | null
          source_id?: string | null
          stage_geometry?: string | null
          stage_material?: string | null
          temperature_note?: string | null
          updated_at?: string
          usage_rights_status?: string
          verification_status?: string
          wsw_crosscheck_result?: string | null
          wsw_design_max_bpd?: number | null
          wsw_design_min_bpd?: number | null
        }
        Update: {
          application_note?: string | null
          bearing_material?: string | null
          bep_efficiency_pct?: number | null
          bep_flow_bpd?: number | null
          bep_head_ft_per_stage?: number | null
          bep_power_hp_per_stage?: number | null
          brand_line?: string | null
          cced_installed_count?: number
          cced_installed_wells?: string | null
          cced_motor_hp_max?: number | null
          cced_motor_hp_min?: number | null
          cced_raw_aliases?: string | null
          cced_stage_max?: number | null
          cced_stage_min?: number | null
          compression_ror_max_bpd?: number | null
          compression_ror_min_bpd?: number | null
          construction_type?: string | null
          created_at?: string
          curve_completeness?: string
          floater_ror_max_bpd?: number | null
          floater_ror_min_bpd?: number | null
          housing_burst_psi?: number | null
          id?: string
          last_review_date?: string | null
          lifecycle_status?: string
          min_casing_in?: number | null
          model?: string
          model_revision?: string | null
          notes?: string | null
          od_in?: number | null
          oem_id?: string
          reference_hz?: number | null
          reference_rpm?: number | null
          reliability_code?: string
          ror_max_bpd?: number | null
          ror_min_bpd?: number | null
          series?: string | null
          shaft_diameter_in?: number | null
          shaft_hp_high_strength?: number | null
          shaft_hp_limit?: number | null
          shaft_material?: string | null
          source_id?: string | null
          stage_geometry?: string | null
          stage_material?: string | null
          temperature_note?: string | null
          updated_at?: string
          usage_rights_status?: string
          verification_status?: string
          wsw_crosscheck_result?: string | null
          wsw_design_max_bpd?: number | null
          wsw_design_min_bpd?: number | null
        }
        Relationships: [
          {
            foreignKeyName: "esp_pump_models_oem_id_fkey"
            columns: ["oem_id"]
            isOneToOne: false
            referencedRelation: "esp_oems"
            referencedColumns: ["id"]
          },
          {
            foreignKeyName: "esp_pump_models_source_id_fkey"
            columns: ["source_id"]
            isOneToOne: false
            referencedRelation: "esp_sources"
            referencedColumns: ["id"]
          },
        ]
      }
      esp_sensor_models: {
        Row: {
          cced_installed_count: number
          created_at: string
          id: string
          max_temp_f: number | null
          measured_channels: string | null
          model: string
          oem_id: string
          pressure_rating_psi: number | null
          reliability_code: string
          source_id: string | null
          updated_at: string
          verification_status: string
        }
        Insert: {
          cced_installed_count?: number
          created_at?: string
          id: string
          max_temp_f?: number | null
          measured_channels?: string | null
          model: string
          oem_id: string
          pressure_rating_psi?: number | null
          reliability_code?: string
          source_id?: string | null
          updated_at?: string
          verification_status?: string
        }
        Update: {
          cced_installed_count?: number
          created_at?: string
          id?: string
          max_temp_f?: number | null
          measured_channels?: string | null
          model?: string
          oem_id?: string
          pressure_rating_psi?: number | null
          reliability_code?: string
          source_id?: string | null
          updated_at?: string
          verification_status?: string
        }
        Relationships: [
          {
            foreignKeyName: "esp_sensor_models_oem_id_fkey"
            columns: ["oem_id"]
            isOneToOne: false
            referencedRelation: "esp_oems"
            referencedColumns: ["id"]
          },
          {
            foreignKeyName: "esp_sensor_models_source_id_fkey"
            columns: ["source_id"]
            isOneToOne: false
            referencedRelation: "esp_sources"
            referencedColumns: ["id"]
          },
        ]
      }
      esp_sources: {
        Row: {
          created_at: string
          document_date: string | null
          document_ref: string | null
          id: string
          last_review_date: string | null
          notes: string | null
          publisher: string
          reliability_code: string
          revision: string | null
          source_type: string
          title: string
          updated_at: string
          usage_rights_status: string
          verification_status: string
        }
        Insert: {
          created_at?: string
          document_date?: string | null
          document_ref?: string | null
          id: string
          last_review_date?: string | null
          notes?: string | null
          publisher: string
          reliability_code: string
          revision?: string | null
          source_type: string
          title: string
          updated_at?: string
          usage_rights_status?: string
          verification_status?: string
        }
        Update: {
          created_at?: string
          document_date?: string | null
          document_ref?: string | null
          id?: string
          last_review_date?: string | null
          notes?: string | null
          publisher?: string
          reliability_code?: string
          revision?: string | null
          source_type?: string
          title?: string
          updated_at?: string
          usage_rights_status?: string
          verification_status?: string
        }
        Relationships: []
      }
      esp_vsd_models: {
        Row: {
          cced_installed_count: number
          created_at: string
          drive_type: string | null
          id: string
          kva_rating: number | null
          model: string
          oem_id: string
          output_amps: number | null
          output_volts: number | null
          reliability_code: string
          source_id: string | null
          transformer_note: string | null
          updated_at: string
          verification_status: string
        }
        Insert: {
          cced_installed_count?: number
          created_at?: string
          drive_type?: string | null
          id: string
          kva_rating?: number | null
          model: string
          oem_id: string
          output_amps?: number | null
          output_volts?: number | null
          reliability_code?: string
          source_id?: string | null
          transformer_note?: string | null
          updated_at?: string
          verification_status?: string
        }
        Update: {
          cced_installed_count?: number
          created_at?: string
          drive_type?: string | null
          id?: string
          kva_rating?: number | null
          model?: string
          oem_id?: string
          output_amps?: number | null
          output_volts?: number | null
          reliability_code?: string
          source_id?: string | null
          transformer_note?: string | null
          updated_at?: string
          verification_status?: string
        }
        Relationships: [
          {
            foreignKeyName: "esp_vsd_models_oem_id_fkey"
            columns: ["oem_id"]
            isOneToOne: false
            referencedRelation: "esp_oems"
            referencedColumns: ["id"]
          },
          {
            foreignKeyName: "esp_vsd_models_source_id_fkey"
            columns: ["source_id"]
            isOneToOne: false
            referencedRelation: "esp_sources"
            referencedColumns: ["id"]
          },
        ]
      }
      esp_well_engineering: {
        Row: {
          bht_f: number | null
          casing_od_in: number | null
          casing_weight_lb_ft: number | null
          created_at: string
          deviation_at_pump_deg: number | null
          perf_bottom_ft: number | null
          perf_top_ft: number | null
          productivity_index_bpd_psi: number | null
          pump_setting_depth_ft: number | null
          reliability_code: string
          reservoir_pressure_psi: number | null
          source_id: string | null
          tubing_id_in: number | null
          updated_at: string
          well_id: string
        }
        Insert: {
          bht_f?: number | null
          casing_od_in?: number | null
          casing_weight_lb_ft?: number | null
          created_at?: string
          deviation_at_pump_deg?: number | null
          perf_bottom_ft?: number | null
          perf_top_ft?: number | null
          productivity_index_bpd_psi?: number | null
          pump_setting_depth_ft?: number | null
          reliability_code?: string
          reservoir_pressure_psi?: number | null
          source_id?: string | null
          tubing_id_in?: number | null
          updated_at?: string
          well_id: string
        }
        Update: {
          bht_f?: number | null
          casing_od_in?: number | null
          casing_weight_lb_ft?: number | null
          created_at?: string
          deviation_at_pump_deg?: number | null
          perf_bottom_ft?: number | null
          perf_top_ft?: number | null
          productivity_index_bpd_psi?: number | null
          pump_setting_depth_ft?: number | null
          reliability_code?: string
          reservoir_pressure_psi?: number | null
          source_id?: string | null
          tubing_id_in?: number | null
          updated_at?: string
          well_id?: string
        }
        Relationships: [
          {
            foreignKeyName: "esp_well_engineering_source_id_fkey"
            columns: ["source_id"]
            isOneToOne: false
            referencedRelation: "esp_sources"
            referencedColumns: ["id"]
          },
          {
            foreignKeyName: "esp_well_engineering_well_id_fkey"
            columns: ["well_id"]
            isOneToOne: true
            referencedRelation: "esp_wells"
            referencedColumns: ["id"]
          },
        ]
      }
      esp_wells: {
        Row: {
          created_at: string
          field_id: string
          id: string
          lift_method: string
          name: string
          pad_area: string | null
          updated_at: string
          well_status: string
        }
        Insert: {
          created_at?: string
          field_id: string
          id: string
          lift_method?: string
          name: string
          pad_area?: string | null
          updated_at?: string
          well_status?: string
        }
        Update: {
          created_at?: string
          field_id?: string
          id?: string
          lift_method?: string
          name?: string
          pad_area?: string | null
          updated_at?: string
          well_status?: string
        }
        Relationships: [
          {
            foreignKeyName: "esp_wells_field_id_fkey"
            columns: ["field_id"]
            isOneToOne: false
            referencedRelation: "esp_fields"
            referencedColumns: ["id"]
          },
        ]
      }
    }
    Views: {
      [_ in never]: never
    }
    Functions: {
      [_ in never]: never
    }
    Enums: {
      [_ in never]: never
    }
    CompositeTypes: {
      [_ in never]: never
    }
  }
}

type DatabaseWithoutInternals = Omit<Database, "__InternalSupabase">

type DefaultSchema = DatabaseWithoutInternals[Extract<keyof Database, "public">]

export type Tables<
  DefaultSchemaTableNameOrOptions extends
    | keyof (DefaultSchema["Tables"] & DefaultSchema["Views"])
    | { schema: keyof DatabaseWithoutInternals },
  TableName extends DefaultSchemaTableNameOrOptions extends {
    schema: keyof DatabaseWithoutInternals
  }
    ? keyof (DatabaseWithoutInternals[DefaultSchemaTableNameOrOptions["schema"]]["Tables"] &
        DatabaseWithoutInternals[DefaultSchemaTableNameOrOptions["schema"]]["Views"])
    : never = never,
> = DefaultSchemaTableNameOrOptions extends {
  schema: keyof DatabaseWithoutInternals
}
  ? (DatabaseWithoutInternals[DefaultSchemaTableNameOrOptions["schema"]]["Tables"] &
      DatabaseWithoutInternals[DefaultSchemaTableNameOrOptions["schema"]]["Views"])[TableName] extends {
      Row: infer R
    }
    ? R
    : never
  : DefaultSchemaTableNameOrOptions extends keyof (DefaultSchema["Tables"] &
        DefaultSchema["Views"])
    ? (DefaultSchema["Tables"] &
        DefaultSchema["Views"])[DefaultSchemaTableNameOrOptions] extends {
        Row: infer R
      }
      ? R
      : never
    : never

export type TablesInsert<
  DefaultSchemaTableNameOrOptions extends
    | keyof DefaultSchema["Tables"]
    | { schema: keyof DatabaseWithoutInternals },
  TableName extends DefaultSchemaTableNameOrOptions extends {
    schema: keyof DatabaseWithoutInternals
  }
    ? keyof DatabaseWithoutInternals[DefaultSchemaTableNameOrOptions["schema"]]["Tables"]
    : never = never,
> = DefaultSchemaTableNameOrOptions extends {
  schema: keyof DatabaseWithoutInternals
}
  ? DatabaseWithoutInternals[DefaultSchemaTableNameOrOptions["schema"]]["Tables"][TableName] extends {
      Insert: infer I
    }
    ? I
    : never
  : DefaultSchemaTableNameOrOptions extends keyof DefaultSchema["Tables"]
    ? DefaultSchema["Tables"][DefaultSchemaTableNameOrOptions] extends {
        Insert: infer I
      }
      ? I
      : never
    : never

export type TablesUpdate<
  DefaultSchemaTableNameOrOptions extends
    | keyof DefaultSchema["Tables"]
    | { schema: keyof DatabaseWithoutInternals },
  TableName extends DefaultSchemaTableNameOrOptions extends {
    schema: keyof DatabaseWithoutInternals
  }
    ? keyof DatabaseWithoutInternals[DefaultSchemaTableNameOrOptions["schema"]]["Tables"]
    : never = never,
> = DefaultSchemaTableNameOrOptions extends {
  schema: keyof DatabaseWithoutInternals
}
  ? DatabaseWithoutInternals[DefaultSchemaTableNameOrOptions["schema"]]["Tables"][TableName] extends {
      Update: infer U
    }
    ? U
    : never
  : DefaultSchemaTableNameOrOptions extends keyof DefaultSchema["Tables"]
    ? DefaultSchema["Tables"][DefaultSchemaTableNameOrOptions] extends {
        Update: infer U
      }
      ? U
      : never
    : never

export type Enums<
  DefaultSchemaEnumNameOrOptions extends
    | keyof DefaultSchema["Enums"]
    | { schema: keyof DatabaseWithoutInternals },
  EnumName extends DefaultSchemaEnumNameOrOptions extends {
    schema: keyof DatabaseWithoutInternals
  }
    ? keyof DatabaseWithoutInternals[DefaultSchemaEnumNameOrOptions["schema"]]["Enums"]
    : never = never,
> = DefaultSchemaEnumNameOrOptions extends {
  schema: keyof DatabaseWithoutInternals
}
  ? DatabaseWithoutInternals[DefaultSchemaEnumNameOrOptions["schema"]]["Enums"][EnumName]
  : DefaultSchemaEnumNameOrOptions extends keyof DefaultSchema["Enums"]
    ? DefaultSchema["Enums"][DefaultSchemaEnumNameOrOptions]
    : never

export type CompositeTypes<
  PublicCompositeTypeNameOrOptions extends
    | keyof DefaultSchema["CompositeTypes"]
    | { schema: keyof DatabaseWithoutInternals },
  CompositeTypeName extends PublicCompositeTypeNameOrOptions extends {
    schema: keyof DatabaseWithoutInternals
  }
    ? keyof DatabaseWithoutInternals[PublicCompositeTypeNameOrOptions["schema"]]["CompositeTypes"]
    : never = never,
> = PublicCompositeTypeNameOrOptions extends {
  schema: keyof DatabaseWithoutInternals
}
  ? DatabaseWithoutInternals[PublicCompositeTypeNameOrOptions["schema"]]["CompositeTypes"][CompositeTypeName]
  : PublicCompositeTypeNameOrOptions extends keyof DefaultSchema["CompositeTypes"]
    ? DefaultSchema["CompositeTypes"][PublicCompositeTypeNameOrOptions]
    : never

export const Constants = {
  public: {
    Enums: {},
  },
} as const
