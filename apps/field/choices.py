class CHOICE:    
    # VARIETY_CHOICES = (
    #             ('CL_XL745', 'CL XL745'),
    #             ('CL111', 'CL111'),
    #             ('CL151', 'CL151'),
    #             ('CLL16', 'CLL16'),
    #             ('CLL17', 'CLL17'),
    #             ('CLM04', 'CLM04'),
    #             ('DG_263L', 'DG-263L'),
    #             ('DIAMOND', 'Diamond'),
    #             ('GEMINI_214_CL', 'Gemini 214 CL'),
    #             ('JEWEL', 'Jewel'),
    #             ('JUPITER', 'Jupiter'),
    #             ('LYNX', 'Lynx'),
    #             ('PROGOLD1', 'ProGold1'),
    #             ('PROGOLD2', 'ProGold2'),
    #             ('PVL01', 'PVL01'),
    #             ('PVL02', 'PVL02'),
    #             ('RT7301', 'RT7301'),
    #             ('RT7321_FP', 'RT7321 FP'),
    #             ('RT7401', 'RT7401'),
    #             ('RT7501', 'RT7501'),
    #             ('RT7521_FP', 'RT7521 FP'),
    #             ('RT7801', 'RT7801'),
    #             ('TITAN', 'Titan'),
    #             ('RT7801', 'RT7801'),
    #             ('XL723', 'XL723'),
    #             ('XP753', 'XP753'),
    #         )

    

    FERT_PRODUCT_CHOICES = (
                ('DAP', 'lb (18-46-0) DAP'),
                ('UREA', 'lb (46-0-0) Urea'),
                ('AMS', 'lb (21-0-0-24) AMS'),
                ('ORBIX', 'oz (8-5-3) Orbix'),
                ('UREA_AMS', 'lb (67-0-0-24) Urea + AMS'),
                ('DAP_AMS', 'lb (39-46-0-24) DAP + AMS'),
                ('UREA_AGROTAIN', 'lb (46-0-0) Urea + Agrotain'),
                ('UREA_CONTAIN', 'lb (46-0-0) Urea + Contain'),
            )
    WATER_SOURCE_CHOICES = (
        ('GROUND', 'Ground'),
        ('SURFACE', 'Surface'),
    )
    FIELD_DESIGN_PLASTIC_USE_SOURCE_CHOICES = (
        ('38', 'Crooked levees = 38-acre inches'),
        ('37', 'Straight levees = 37-acre inches'),
        ('29', 'Straight levees + MIRI 29-acre inches'),
        ('22', 'Zero grade = 22-acre inches'),
        ('0', 'Precision-grade Row Rice'),
    )
    STRAW_BURNT_REMOVED_CHOICES = (
        ('YES', 'Yes'),
        ('NO', 'No'),
    )
    RESIDUE_TILLAGE_CROP_MGMT_CHOICES = (
        ('1', 'Field burnt-full tillage'),
        ('2', 'Residue retained-full tillage'),
        ('3', 'Residue retained-full tillage-cover crop'),
        ('4', 'Residue retained (reduced tillage)'),
        ('5', 'Residue retained (reduced tillage)-cover crop'),
        ('6', 'Residue burnt (reduced tillage)'),
        ('7', 'Residue burnt (reduced tillage)-cover crop'),
        ('8', 'Residue burnt (no-tillage)-cover crop'),
        ('9', 'no-tillage'),
    )


    FARM_GROUP_CHOICES = (
    ('farm', 'Farm'),
    ('grower', 'Grower'), 
	('crop', 'Crop'), 
	('variety', 'Variety'),
	('crop_tech', 'Crop Tech'),
	('burndown_chemical', 'Burndown Chemical'), 
	('preemergence_chemical', 'Preemergence Chemical'), 
	('stand_count', 'Stand Count'), 
	('fungicide_micronutrients', 'Fungicide Micronutrients'), 
	('insecticide_application', 'Insecticide Application'), 
	('litter', 'Litter'),
	('pre_fert_product', 'Pre Fert Product'),
	('early_post_fert_product', 'Early Post Fert Product'),
	('foliar_fert_app_product', 'Foliar Fert App Product'), 
	('pre_flood_fert_product', 'Pre Flood Fert Product'),  
	('post_flood_midseason_fert_product', 'Post Flood Midseason Fert Product'),
	('post_flood_midseason_fert_product2', 'Post Flood Midseason Fert Product2'),
	('post_flood_midseason_fert_product3', 'Post Flood Midseason Fert Product3'),
	('boot_fertilizer_product', 'Boot Fertilizer Product'),
	('water_source', 'Water Source'),
	('measured_water_use', 'Measured Water Use'),  
	('field_design_and_use_of_plastic_pipe', 'Field Design And Use Of Plastic Pipe'),
	('previous_crop', 'Previous Crop'), 
	('straw_burnt_or_residue_removed', 'Straw Burnt Or Residue Removed'),
	('straw_residue_tillage_and_cover_crop_management', 'Straw Residue Tillage And Cover Crop Management'),  
	('tillage_equipment_and_passes_or_fuel_usage_for_tillage', 'Tillage Equipment And Passes Or Fuel Usage For Tillage'),
    )
