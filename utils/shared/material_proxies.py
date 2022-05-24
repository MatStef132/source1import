# Proxy to Dynamic Expression
# https://developer.valvesoftware.com/wiki/List_Of_Material_Proxies
# https://developer.valvesoftware.com/wiki/Dota_2_Workshop_Tools/Materials/Dynamic_Material_Expressions

try:
    from .keyvalues1 import VDFDict
except ImportError:
    from keyvalues1 import VDFDict
    
class Proxies(VDFDict): pass

def add(srcvar1, srcvar2, **_):         return f"{srcvar1} + {srcvar2}"
def multiply(srcvar1, srcvar2, **_):    return f"{srcvar1} * {srcvar2}"
def substract(srcvar1, srcvar2, **_):   return f"{srcvar1} - {srcvar2}"
def divide(srcvar1, srcvar2, **_):      return f"{srcvar1} / {srcvar2}"

def equals(srcvar1, **_):   return f"{srcvar1}"
def abs(srcvar1, **_):      return f"abs({srcvar1})"
def frac(srcvar1, **_):     return f"frac({srcvar1})"

_int = int
def int(srcvar1, **_):
    return f"(frac({srcvar1}) >= 0.5 ? ceil({srcvar1}) : floor({srcvar1}))"

def clamp(srcvar1, minval, maxval, **_):
    return f"clamp({srcvar1}, {minval}, {maxval})"

def lessorequal(lessequalvar, greatervar, srcvar1, srcvar2, **_):
    return f"({srcvar1} <= {srcvar2}) ? {lessequalvar} : {greatervar}"

def selectfirstifnonzero(srcvar1, srcvar2, **_):
    return f"({srcvar1} != 0) ? {srcvar1} : {srcvar2}"

def wrapminmax(srcvar1, minval, maxval, **_):
    if ( maxval <= minval ): # Bad input, just return the min
        return f"{minval}"
    else:
        expr = (
            f"flResult = ( {srcvar1} - {minval} ) / ( {maxval} - {minval} )",
            f"(flResult >= 0) ? flResult = flResult - ({int('flResult')}) : flResult = flResult - ({int('flResult')}) - 1",
            f"(flResult * ( {maxval} - {minval} )) + {minval}"
        )
		            #f"flResult = flResult + minval;
    return expr
def remapvalclamp(srcvar1, range_in_min = 0, range_in_max = 1, range_out_min = 0, range_out_max = 1, **_):

    #if ( A == B ) return fsel( val - B , D , C ); // fsel(c,x,y) { ( (c) >= 0 ? (x) : (y) ) }
	#float cVal = (val - A) / (B - A);
	#cVal = clamp<float>( cVal, 0.0f, 1.0f );
	#return C + (D - C) * cVal;

    A, B, C, D = range_in_min, range_in_max, range_out_min, range_out_max
    expr = (
        f"remapvalclamp_temp1 = ({srcvar1} - {B}) >= 0 ? {D} : {C}",
        f"remapvalclamp_temp2 = {C} + ({D} - {C}) * {clamp((srcvar1 - A) / (B - A), 0, 1)}",
        f"{A} == {B} ? remapvalclamp_temp1 : remapvalclamp_temp2",
    )
    return expr

    #if ( A == B )
	#	return f"({val} - {B}) >= 0 ? {D} : {C}"
	#return f"{C} + ({D} - {C}) * {clamp((srcvar1 - A) / (B - A), 0, 1)}"

def exponential( minval, maxval, srcvar1, offset = 0, scale = 1, **_):
    return f"clamp({scale} * pow(2.71828, {srcvar1} + {offset}), {minval}, {maxval})"

def sine(sineperiod, sinemin = -1, sinemax = 1, timeoffset = 0, **_):
    return f"( {sinemax} - {sinemin} ) * (( sin( 2.0 * 3.14159265358979323846264338327950288 * (time() - {timeoffset}) / {sineperiod} ) * 0.5 ) + 0.5) + {sinemin}"

def linearramp(rate = 1, initialvalue = 0, **_):
    return f"( {rate} * time() + {initialvalue} )"

def entityrandom(**_): # temporary
    return "0"

def currenttime(**_):
    return "time()"

def uniformnoise(minval, maxval, mean, **_):
    return f"random({minval}, {maxval})"

def gaussiannoise(minval, maxval,  halfwidth, mean, **_):
    return f"random({minval}, {maxval})"

def texturetransform(centervar, scalevar, rotatevar, translatevar, **_):
    return f"float2({translatevar[0]}, {translatevar[1]})"
    return f"float2({scalevar[0]}, {scalevar[1]})"

def texturescroll(texturescrollvar, texturescrollrate, texturescrollangle, **_):
    return f"float2({texturescrollrate} * cos({texturescrollangle}, {texturescrollrate} * sin({texturescrollrate}))"

def get_resultvar(proxy: dict):
    for key, val in proxy.items():
        if key == "resultvar":
            return val
    return None

def search_res(proxies, result: str):
    for proxy in proxies:
        if result == get_resultvar(proxies[proxy]):
            return proxy

class DynamicExpression:
    def __init__(self):
        #self.parent = parent

        # Lists of lines of code
        self.constants = {}
        self.defined_variables = []
        self.expression_list = []

    def add_expression(self, expression): # bottom to top
        self.expression_list.insert(0, expression)
    
    def __repr__(self):
        s: str = "// Auto-Generated by Source1Import\n\n"
        for k, v in self.constants.items():
            s += f"{k} = {v};\n"
        for expression in self.expression_list:
            ";\n".join(expression.splitlines()) # multi-line expressions
            s += f"{expression};\n"
        return repr(s)#repr(s)

    def __str__(self) -> str:
        return str(self.__repr__())

def FormDynamicExpression(proxy: str, proxyParams: dict, mainResultVar: str, known, KeyValues, vmtProxies) -> DynamicExpression:
 
    undefined_vars = [mainResultVar]

    dynEx = DynamicExpression()

    for var in undefined_vars:
        #print(var)
        
        if var in dynEx.defined_variables:
            continue

        mainResult = (var == mainResultVar)
        #print(var, undefined_vars)

        if not mainResult: # input variable of preceding proxy
            proxy = search_res(vmtProxies, var)
            if not proxy:
                #print("no proxy found for", var)
                continue
            proxyParams = vmtProxies[proxy]

        for key, value in proxyParams.items():
            if key == "resultvar": continue
            if type(value) is str and value.startswith("$"):
                if value in known:
                    proxyParams[key] = known[value] # does nott work
                else:
                    #proxyParams[key] = value
                    undefined_vars.append(proxyParams[key])
                    #search = True
        try:
            expression = globals()[proxy](**proxyParams)
        except TypeError:
            continue
        except KeyError:
            print("Missing func", proxy)
            continue

        if not mainResult:
            expression = f"{var} = " + expression
            #if var in dynamicEx.undefined_variables:
            #    dynamicEx.undefined_variables.remove(var)

        dynEx.add_expression(expression)
        dynEx.defined_variables.append(var)
    
    for var in undefined_vars[:]:
        if var in dynEx.defined_variables:
            undefined_vars.remove(var)
            continue

        if var in KeyValues:
            dynEx.constants[var] = KeyValues[var]
            undefined_vars.remove(var)

    return dynEx

def ProxiesToDynamicParams(vmtProxies: VDFDict, known, KeyValues) -> tuple[dict, dict[str, DynamicExpression]]:
    vmatDynamicParams: dict[str, DynamicExpression] = {}
    vmatKeyValues: dict = {}

    for proxy, proxyParams in vmtProxies.items():
        if proxy == "animatedtexture":
            # sequential animation, get framerate
            if proxyParams["animatedtextureframenumvar"] != "$frame":
                continue
            vmatKeyValues["F_TEXTURE_ANIMATION"] = 1
            vmatKeyValues["g_flAnimationTimePerFrame"] = 1 / float(proxyParams["animatedtextureframerate"])
            continue
        # resultvar needs to be a vmt $key that can be translated
        if (resultvar:=get_resultvar(proxyParams)) not in known:
            continue
        
        # scripted animation sequence
        if resultvar == "$frame":
            vmatKeyValues["F_TEXTURE_ANIMATION"] = 1
            vmatKeyValues["F_TEXTURE_ANIMATION_MODE"] = 2

        dynEx = FormDynamicExpression(proxy, proxyParams, resultvar, known, KeyValues, vmtProxies)

        dpKey = known[resultvar] # g_vColorTint
        vmatDynamicParams[dpKey] = repr(dynEx).strip("'") # "clamp(random(1), 0.4, 0.6)"

    return vmatKeyValues, vmatDynamicParams


M_PI = 3.14159265358979323846264338327950288
if __name__ == "__main__":
    import unittest
 
    class Test_KeyValues(unittest.TestCase):
        def test1(self):
            known2 = {"$color": "g_vColor", "$alpha": "g_flOpacity"}
            KeyValue5 = {
                "$addoutput": 0,
                "$loeoutput": 0,
                "$noisesignal": 0,
                "$noisegate": 0.6,
                "$zero": 0,
                "$sinewaveoutput": 0,
                "$one": 1,
                "proxies": Proxies({
                    "clamp": {
                        "minval": .1,
                        "maxval": 1,
                        "srcvar1": "$addoutput",
                        "resultvar": "$color",
                    },
                    "add": {
                        "srcvar1": "$sinewaveoutput", 
                        "srcvar2": "$loeoutput",
                        "resultvar": "$addoutput",
                    },
                    "lessorequal": {
                        "lessequalvar": "$zero",
                        "greatervar": "$one",
                        "srcvar1": "$noisesignal",
                        "srcvar2": "$noisegate",
                        "resultvar": "$loeoutput",
                    },
                    "gaussiannoise": {
                        "minval": .1,
                        "maxval": 1,
                        "halfwidth": .5,
                        "mean": 1,

                        "resultvar": "$noisesignal",
                    },
                    "sine": {    
                        "sinemin": 0,
                        "sinemax": 6,
                        "sineperiod": 8,
                        "resultvar": "$sinewaveoutput",
                    },
                    "substract": {
                        "srcvar1": 5,
                        "srcvar2": 2,
                        "resultvar": "$alpha",
                    }
                }),
            }
            expected_result = {
                'g_vColor': r'// Auto-Generated by Source1Import\n\n$zero = 0;\n$one = 1;\n$noisegate = 0.6;\n$noisesignal = random(0.1, 1);\n$loeoutput = ($noisesignal <= $noisegate) ? $zero : $one;\n$sinewaveoutput = ( 6 - 0 ) * (( sin( 2.0 * 3.14159265358979323846264338327950288 * (time() - 0) / 8 ) * 0.5 ) + 0.5) + 0;\n$addoutput = $sinewaveoutput + $loeoutput;\nclamp($addoutput, 0.1, 1);\n',
                'g_flOpacity': r'// Auto-Generated by Source1Import\n\n5 - 2;\n'
            }
            _, result = ProxiesToDynamicParams(KeyValue5["proxies"], known2, KeyValue5)
            self.maxDiff = None
            self.assertEqual(result, expected_result)
    unittest.main()
#def Sinee(sineperiod, sinemin = -1, sinemax = 1, timeoffset = 0):
#    quit()
    #return """
    #m_Sine_sinemin = 0;
    #m_Sine_sinemax = 6;
    #m_Sine_sineperiod = 5;
    #m_Sine_timeoffset = 0;
    #_proxy_sinewaveOutput = ( m_Sine_sinemax - m_Sine_sinemin ) * (( sin( 2.0 * 3.14159265358979323846264338327950288 * (time() - m_Sine_timeoffset) / m_Sine_sineperiod ) * 0.5 ) + 0.5) + m_Sine_sinemin;
    #"""