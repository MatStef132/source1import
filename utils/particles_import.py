import shared.datamodel as dmx
if __name__ is None:
    import utils.shared.datamodel as dmx

from pathlib import Path

class resource(str): pass  # kv3 resource

class dynamicparam(str): pass
class maxof(dynamicparam): pass
class minof(dynamicparam): pass
#TODO: are arrays different from vectors? vec seems to have no newlines and no comma at end

pcf_to_vpcf = {
    # name/functionName -> class

    'renderers': ( 'm_Renderers', {
        'render_sprite_trail': '',
        'render_animated_sprites':  'C_OP_RenderSprites',
            'animation rate': 'm_flAnimationRate',
            'second sequence animation rate': '',
            'Visibility Proxy Radius': '',
            'Visibility Proxy Input Control Point Number': '',
            'Visibility input distance maximum': '',
            'Visibility input distance minimum': '',
            'Visibility Radius Scale maximum': maxof('m_flRadiusScale'),
            'Visibility Alpha Scale maximum': maxof('m_flAlphaScale'),
            'Visibility Alpha Scale minimum': minof('m_flAlphaScale'),
            'Visibility input minimum': '',
            'Visibility input maximum': '',
            'Visibility Radius Scale minimum': minof('m_flRadiusScale'),
            'use animation rate as FPS': '',
            'animation_fit_lifetime': '',
            'orientation_type': 'm_nOrientationType',
            'length fade in time': '',
            'min length': 'm_flMinSize',
            'max length': 'm_flMaxSize',
            'constrain radius to length': '',
            'ignore delta time': '',
    }),
    
    'operators': ('m_Operators', {
        'Lifespan Decay': 'C_OP_Decay',
        'Radius Scale': 'C_OP_InterpolateRadius',
            'radius_start_scale': 'm_flEndScale',
            'radius_end_scale': 'm_flStartScale',
            'scale_bias': '',
            'end_time': '',
            'ease_in_and_out': '',
        'Alpha Fade In Random': 'C_OP_FadeIn',
            'proportional 0/1': 'm_bProportional',
            'fade out time min': 'm_flFadeOutTimeMin',
            'fade out time max': 'm_flFadeOutTimeMax',
            'fade in time min': '',
            'fade in time max': '',
            'ease in and out': 'm_bEaseInAndOut',
        'Alpha Fade Out Random': 'C_OP_FadeOut',
            'proportional 0/1': 'm_bProportional',
            'fade out time min': 'm_flFadeOutTimeMin',
            'fade out time max': 'm_flFadeOutTimeMax',
            'ease in and out': 'm_bEaseInAndOut',
            'fade bias': '',
        'Movement Basic': 'C_OP_BasicMovement',
            'gravity': 'm_Gravity',
            'drag': '',
            'operator end fadeout': '',
            'operator start fadeout': '',
            'operator end fadein': '',
            'operator start fadein': '',
        'Movement Dampen Relative to Control Point': '',
            'dampen scale': '',
            'falloff range': '',
        'Alpha Fade and Decay': '',
            'end_fade_in_time': '',
            'start_alpha': '',
            'start_fade_out_time': '',
            'end_fade_out_time': '',
        'Rotation Basic': '',
        'Oscillate Scalar': '',
            'oscillation frequency max': '',
            'oscillation frequency min': '',
            'oscillation rate max': '',
            'oscillation rate min': '',
            'oscillation field': '',
            'oscillation multiplier': '',
        'Oscillate Vector': '',
        'Movement Lock to Control Point': '',
            'lock rotation': '',
            'start_fadeout_min': '',
            'start_fadeout_max': '',
            'end_fadeout_min': '',
            'end_fadeout_max': '',
        'Cull when crossing sphere': '',
            'Cull Distance': '',
            'Cull plane offset': '',
        'Remap Distance to Control Point to Scalar': '',
            'output maximum': '',
            'output minimum': '',
            'output field': '',
            'distance maximum': '',
            'distance minimum': '',
        'Color Fade': '',
            'color_fade': '',
            'fade_start_time': '',
            'fade_end_time': '',
        'Rotation Spin Roll': '',
            'spin_rate_degrees': '',
            'spin_stop_time': '',
            'operator strength random scale max': '',
            'operator strength random scale min': '',
            'operator strength scale seed': '',
            'spin_rate_min': '',
        'Set Control Point Positions': '',
            'First Control Point Location': '',
        'Alpha Fade In Simple': '',
            'proportional fade in time': '',
        'Cull when crossing plane': '',
        'Set child control points from particle positions': '',
            '# of control points to set': '',
    }),

    'initializers': ('m_Initializers', {
        'Position Within Sphere Random': 'C_INIT_CreateWithinSphere',
            'speed_max': 'm_fSpeedMax',
            'speed_min': 'm_fSpeedMin',
            'distance_min': 'm_fRadiusMin',
            'distance_max': 'm_fRadiusMax',
            'speed_in_local_coordinate_system_max': 'm_LocalCoordinateSystemSpeedMax',
            'speed_in_local_coordinate_system_min': 'm_LocalCoordinateSystemSpeedMin',
            'distance_bias': 'm_vecDistanceBias',
            'distance_bias_absolute_value': 'm_vecDistanceBiasAbs',
            'speed_random_exponent': 'm_fSpeedRandExp',
            'control_point_number': 'm_nControlPointNumber',
            'bias in local system': 'm_bLocalCoords',
            'randomly distribute to highest supplied Control Point': '',
            'randomly distribution growth time': 'm_flEndCPGrowthTime',

        'Lifetime Random': 'C_INIT_RandomLifeTime',
            "lifetime_min": 'm_fLifetimeMin',
            "lifetime_max": 'm_fLifetimeMax',
            'lifetime_random_exponent': 'm_fLifetimeRandExponent',

        'Color Random': 'C_INIT_RandomColor',
            'tint clamp max': 'm_TintMax',
            'tint clamp min': 'm_TintMin',
            'tint update movement threshold': 'm_flUpdateThreshold',
            'light amplification amount': 'm_flLightAmplification',
            'color1': 'm_ColorMin',
            'color2': 'm_ColorMax',
            'tint_perc': 'm_flTintPerc',
            'tint blend mode': 'm_nTintBlendMode',

        'Rotation Random': 'C_INIT_RandomRotation',
            'randomly_flip_direction': 'm_bRandomlyFlipDirection',
            'rotation_offset_max': 'm_flDegreesMin',
            'rotation_offset_min': 'm_flDegreesMax',
            'rotation_initial': 'm_flDegrees',

        'Alpha Random': 'C_INIT_RandomAlpha',
            "alpha_max": 'm_nAlphaMin',
            "alpha_min": 'm_nAlphaMax',

        'Position Modify Offset Random': 'C_INIT_PositionOffset',
            'offset max': 'm_OffsetMin',
            'offset min': 'm_OffsetMax',
            'offset in local space 0/1': 'm_bLocalCoords',
            'offset proportional to radius 0/1': 'm_bProportional',
        'Sequence Random': 'C_INIT_RandomSequence',
            'sequence_max': 'm_nSequenceMax',
            'sequence_min': 'm_nSequenceMin',
            'shuffle': 'm_bShuffle',
        'Sequence Two Random': 'C_INIT_RandomSecondSequence',
        'Radius Random': 'C_INIT_RandomRadius',
            'radius_min': 'm_flRadiusMin',
            'radius_max': 'm_flRadiusMax',
            'radius_random_exponent': 'm_flRadiusRandExponent',
        'Rotation Speed Random': 'C_INIT_RandomRotationSpeed',
            'rotation_speed_random_min': 'm_flDegreesMin',
            'rotation_speed_random_max': 'm_flDegreesMax',
        'Position Within Box Random': '',
            'max': 'm_vecMax',
            'min': 'm_vecMin',
        'Rotation Yaw Flip Random': '',
            'Flip Percentage': 'm_flPercent',
        'remap initial scalar': '',
            'input minimum': 'm_flInputMin',
            'input maximum': 'm_flInputMax',
            'output minimum': 'm_flOutputMin',
            'output maximum': 'm_flOutputMax',
            'output is scalar of initial random range': '',
            'output field': 'm_nFieldOutput',
        'Position Modify Warp Random': '',
            'warp min': '',
            'warp max': '',
            'warp transition time (treats min/max as start/end sizes)': '',
            'warp transition start time': '',
        'Velocity Noise': '',
            'Spatial Noise Coordinate Scale': '',
            'Absolute Value': '',
            'Time Noise Coordinate Scale': '',
            'Apply Velocity in Local Space (0/1)': '',
        'Trail Length Random': '',
            'length_min': '',
            'length_max': '',
        'Lifetime From Sequence': '',
            'Frames Per Second': '',
            'operator strength random scale max': '',
            'operator strength scale seed': '',
        'Remap Initial Scalar': '', # 'remap initial scalar' wtf
            'input minimum': '',
            'emitter lifetime end time (seconds)': '',
            'emitter lifetime start time (seconds)': '',
        'Remap Initial Distance to Control Point to Scalar': '',
            'distance maximum': '',
        'Position Along Ring': '',
            'initial radius': '',
            'min initial speed': '',
            'max initial speed': '',
            'even distribution': '',
            'XY velocity only': '',
            'thickness': '',
        'Velocity Random': '',
        'Position From Parent Particles': '',
        'Remap Scalar to Vector': '',
        'lifetime from sequence': '',
        'Scalar Random': '',
    }),

    # this seems more advanced
    # emission_start_time (float) "14"->>
    # m_flStartTime = 
	# {
	# 	m_nType = "PF_TYPE_LITERAL"
	# 	m_flLiteralValue = 14.0
	# }
    
    'emitters': ('m_Emitters', {
        'emit_instantaneously': ('C_OP_InstantaneousEmitter', {
            'num_to_emit': 'm_nParticlesToEmit',
            'emission_start_time': 'm_flStartTime',
            'maximum emission per frame': 'm_nMaxEmittedPerFrame',
            # _nParticlesToEmit = 
			# {
			# 	m_nType = "PF_TYPE_RANDOM_UNIFORM"
			# 	m_flRandomMin = 80.0
			# 	m_flRandomMax = 160.0
			# 	m_nRandomMode = "PF_TYPE_RANDOM_UNIFORM" # not needed i think
			# }
            # probably modified? why did you do this mr csgo dev
            # "num_to_emit" "int" "180"
            # "num_to_emit_minimum" "int" "100"
            'num_to_emit_minimum': minof('m_nParticlesToEmit'), # proc 
        }),
        'emit_continuously': ('C_OP_ContinuousEmitter', {
            'emission_duration': dynamicparam('m_flEmissionDuration'),
            'emission_rate': dynamicparam('m_flEmitRate'),
            'emission_start_time': dynamicparam('m_flStartTime'),
            'operator end fadein': '',
            'scale emission to used control points': 'm_flScalePerParentParticle', # not sure
            'operator end fadeout': '',
            'operator start fadeout': '',
            'use parent particles for emission scaling': '',
            'operator fade oscillate': '',
        }),
        'emit noise': ('C_OP_NoiseEmitter', {
            'emission minimum': 'm_flOutputMin',
            'emission maximum': 'm_flOutputMax',
        }),
        'emit to maintain count': ('C_OP_MaintainEmitter', {
            'count to maintain': 'm_iMaintainCount',
        }),
    }),
    'forces':      ('m_ForceGenerators', {

    }),
    'constraints':  ('m_Constraints', {

    }),

    'children': 'm_Children',
    'material': ('m_Renderers', 'm_hTexture'), # TODO FIXME

    # bare replacement
    'batch particle systems': '',
    'aggregation radius': '',
    'view model effect': '',
    'screen space effect': '',
    'maximum time step': '',
    'minimum rendered frames': '',
    'minimum simulation time step': '',
    'freeze simulation after time': '',
    'preventNameBasedLookup':           '',
    'max_particles':                    'm_nMaxParticles',
    'initial_particles':                'm_nInitialParticles',
    'cull_replacement_definition':      '',
    'fallback replacement definition':  'm_hFallback', # not a string on pcf, its value is an id
    'fallback max count':               'm_nFallbackMaxCount',
    'radius':                           'm_flConstantRadius',
    'color':                            'm_ConstantColor',
    'maximum draw distance':            'm_flMaxDrawDistance',
    'time to sleep when not drawn':     'm_flNoDrawTimeToGoToSleep',
    'Sort particles':                   'm_bShouldSort',
    'bounding_box_min':                 'm_BoundingBoxMin',
    'bounding_box_max':                 'm_BoundingBoxMax',

}

explosions_fx = Path(r'D:\Users\kristi\Documents\GitHub\source1import\utils\shared\particles\explosions_fx.pcf')
lightning = Path(r'D:\Users\kristi\Documents\GitHub\source1import\utils\shared\particles\lighting.pcf')

x = dmx.load(explosions_fx)

def is_valid_pcf(x: dmx.DataModel):
    return ('particleSystemDefinitions' in x.elements[0].keys() and
            x.elements[1].type == 'DmeParticleSystemDefinition'      
        )

def tests():
    print(x.elements[0].keys())
    print(x.elements[1].type)

def pcfkv_convert(key, value):

    if not (vpcf_translation:= pcf_to_vpcf.get(key)):
        if vpcf_translation is None:
            un(key, '_generic')
        return

    outKey, outVal = key, value

    if isinstance(vpcf_translation, str):  # simple translation
        if value == []: return
        #if vpcf_translation =='m_Children':
        #    print(type(value))
        #    quit()
        if isinstance(value, dmx._ElementArray):
            if key == 'children':
                outVal = []
                for child in value:
                    if not child.type == 'DmeParticleChild': # TODO dont need
                        continue
                    child_resrc_ref = resource(child.name) # TODO: proper resource path
                    outVal.append(dict(m_ChildRef = child_resrc_ref))
                return vpcf_translation, outVal

            else:
                print('Warning:', key, "is an unhandled element_array")
                return

        return vpcf_translation, value
    elif isinstance(vpcf_translation, tuple):
        if isinstance(vpcf_translation[1], str):  # insert to another dict
            return
        elif not isinstance(vpcf_translation[1], dict):
            return
    
        if not isinstance(value, list):
            print(key, "is not a ot a list?", value)
            return
        outKey, vpcf_translation = vpcf_translation
        outVal = []
        for opitem in value:
            bWasTuple = False
            if not (className := vpcf_translation.get(opitem.name)):
                if className is None:
                    un(opitem.name, outKey)
                continue
            if isinstance(className, tuple):
                className, vpcf_translation = className
                bWasTuple = True
            subKV = { '_class': className }

            for key, value in opitem.items():
                if key == 'functionName':
                    continue
                    
                if bWasTuple:
                    value = {'m_nType': "PF_TYPE_LITERAL",'m_flLiteralValue': value}

                if subkey:=vpcf_translation.get(key):
                    subKV[subkey] = value
                elif subkey is None:
                    un(key, opitem.name)

            outVal.append(subKV)

    return outKey, outVal

def dict_to_kv3_text(
        kv3dict: dict,
        header = '<!-- kv3 encoding:text:version{e21c7f3c-8a33-41c5-9977-a76d3a32aa0d} format:generic:version{7412167c-06e9-4698-aff2-e63eb59037e7} -->'
    ):
    kv3 = header + '\n'

    def obj_serialize(obj, indent = 1, dictKey = False):
        preind = ('\t' * (indent-1))
        ind = ('\t' * indent)
        if obj is None:
            return 'null'
        elif isinstance(obj, bool):
            if obj: return 'true'
            return 'false'
        elif isinstance(obj, str):
            return '"' + obj + '"'
        elif isinstance(obj, resource):
            print(obj, "Is resource:")
            return f'resource:"{obj}"'
        elif isinstance(obj, list):
            s = '['
            if any(isinstance(item, dict) for item in obj):
                s = f'\n{preind}[\n'
                for item in obj:
                    s += (obj_serialize(item, indent+1) + ',\n')
                return s + preind + ']\n'

            return f'[{", ".join((obj_serialize(item, indent+1) for item in obj))}]'
        elif isinstance(obj, dict):
            s = preind + '{\n'
            if dictKey:
                s = '\n' + s
            for key, value in obj.items():
                #if value == [] or value == "" or value == {}: continue
                s +=  ind + f"{key} = {obj_serialize(value, indent+1, dictKey=True)}\n"
            return s + preind + '}'
        else: # likely an int, float
            return str(obj)

    if not isinstance(kv3dict, dict):
        raise TypeError("Give me a dict, not this %s thing" % repr(kv3dict))
    kv3 += obj_serialize(kv3dict)

    return kv3


unt = {}
def un(val, t):
    val, t = str(val), str(t)
    try:
        if t not in unt[val]:
            unt[val].append(t)
    except (KeyError, AttributeError):
        unt[val] = list()
        unt[val].append(t)

if is_valid_pcf(x):
    print('valid')
    for datamodel in x.find_elements(elemtype='DmeParticleSystemDefinition'):
        print(datamodel.type, datamodel.name)
        
        vpcf = dict(_class = "CParticleSystemDefinition")
        for key, value in datamodel.items():
            if converted_kv:= pcfkv_convert(key, value):
                vpcf[converted_kv[0]] = converted_kv[1]
        
        
        header = '<!-- kv3 encoding:text:version{e21c7f3c-8a33-41c5-9977-a76d3a32aa0d} format:vpcf26:version{26288658-411e-4f14-b698-2e1e5d00dec6} -->'
        print(dict_to_kv3_text(vpcf, header))
        #break
        #for element in datamodel:
        #    print(f'  {element}')
    generics = list()
    dd = {}
    for n, nn in unt.items():
        #for nn in unt[n]:
        #    print(f'{nn})
        if '_generic' in nn:
            generics.append(str(n))
            continue
        elif nn[0]:#.startswith('m_'):
            try:
                dd[nn[0]].append(n)
            except (KeyError, AttributeError):
                dd[nn[0]] = list()
                dd[nn[0]].append(n)
            continue

        print(f"'{n}': '',  #", nn)
    
    for k, v in dd.items():
        print('------', k)
        for n in v:
            print(f"'{n}': '',")

    for n in generics:
        print(f"'{n}': '',")
else:
    print("Invalid!!")
    #tests()
