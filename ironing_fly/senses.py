"""Local egocentric 16x8 retina + contact and heat. No wrinkle target oracle.

The renderer/feature-to-cell mapping is engineered. It is not a validated fly
optic-lobe model; stimulation enters identified visual projection neurons.
"""
import numpy as np
from scipy.ndimage import map_coordinates

class Senses:
    def __init__(self, version=1):
        if version not in (1, 2):
            raise ValueError('Unknown sensory encoder version')
        self.version = version
        self.lookahead = .25 if version == 2 else .45
        self.previous = None
        self.last = {}

    def observe(self, cloth, heading, max_hz):
        # Local top-down image ahead of the iron, in its own reference frame.
        lateral, forward = np.meshgrid(np.linspace(-.25,.25,16),np.linspace(.025,self.lookahead,8))
        direction = np.array([np.cos(heading),np.sin(heading)])
        right = np.array([-direction[1],direction[0]])
        wx = cloth.position[0]+forward*direction[0]+lateral*right[0]
        wy = cloth.position[1]+forward*direction[1]+lateral*right[1]
        coords = np.array([wy.ravel()*(cloth.n-1),wx.ravel()*(cloth.n-1)])
        # Simple raking-light rendering. No global strongest-wrinkle lookup.
        gy,gx = np.gradient(cloth.wrinkle)
        image = np.clip(.72+gx*1.8-gy*1.3-cloth.wrinkle*.35-cloth.scorch*.5,.05,.95)
        image = np.where(cloth.mask,image,.35)
        retina = map_coordinates(image,coords,order=1,mode='constant',cval=.15).reshape(8,16)
        contact_image = map_coordinates(cloth.mask.astype(float),coords,order=0,mode='constant',cval=0).reshape(8,16)
        motion = np.zeros_like(retina) if self.previous is None else np.abs(retina-self.previous)
        self.previous = retina.copy()
        gy,gx = np.gradient(retina)
        edges = np.hypot(gx,gy)
        i,j = np.clip(np.rint(cloth.position[::-1]*(cloth.n-1)),0,cloth.n-1).astype(int)
        contact = float(cloth.mask[i,j])*cloth.pressure
        heat = float(np.clip((cloth.heat[i,j]-35)/85,0,1))
        channels = {}
        for side,sl in [('left',slice(0,8)),('right',slice(8,16))]:
            contrast = float(np.clip(edges[:,sl].mean()*4,0,1))
            flow = float(np.clip(motion[:,sl].mean()*12,0,1))
            boundary = float(1-contact_image[:,sl].mean())
            channels[f'LC11_{side}'] = max_hz*(.12+.88*contrast)
            channels[f'LPLC1_{side}'] = max_hz*(.08+.72*boundary+.2*flow)
            channels[f'LC4_{side}'] = max_hz*.65*flow
            channels[f'LPLC2_{side}'] = max_hz*.65*flow
            channels[f'LLPC1_{side}'] = max_hz*flow
            for cell in ['LC12','LPC1','LC10a','LC10d']:
                channels[f'{cell}_{side}'] = max_hz*(.1+.9*contrast)
            channels[f'contact_{side}'] = max_hz*.6*contact
            channels[f'thermal_{side}'] = max_hz*heat
        self.last = {'retina':retina.round(4).ravel().tolist(),'retina_width':16,'retina_height':8,
                     'version':self.version,'lookahead_board_widths':self.lookahead,
                     'channels_hz':channels,'local_temperature_c':float(cloth.heat[i,j]),'contact':contact,
                     'description':'Local luminance/edge and temporal-change features; no selected wrinkle target or fabric label.'}
        return channels

class MotorDecoder:
    """Fixed neural-to-tool adapter; no expert imitation or direct sensory input.

    DN activity is not an ironing command in a fly. The yaw/speed/pressure/steam
    equations below are explicit engineered units and gains. No force is applied
    with silent output. Escape-like DN activity lifts; MDNs oppose forward drive.
    """
    def __init__(self, version=3):
        if version not in (1, 2, 3):
            raise ValueError('Unknown motor adapter version')
        self.version = version

    def decode(self, rates, heading, dt=.02):
        left,right = rates.get('DNa02_left',0.),rates.get('DNa02_right',0.)
        approach_l,approach_r = rates.get('DNp66_left',0.),rates.get('DNp66_right',0.)
        avoid_l,avoid_r = rates.get('DNp03_left',0.),rates.get('DNp03_right',0.)
        turn = float(np.tanh((right-left+approach_r-approach_l+avoid_l-avoid_r)/40))
        forward = (rates.get('DNp09_left',0.)+rates.get('DNp09_right',0.))/2
        forward += (approach_l+approach_r)/2
        backward = (rates.get('MDN_left',0.)+rates.get('MDN_right',0.))/2
        escape = max(rates.get('DNp01_left',0.),rates.get('DNp01_right',0.))
        motor = (rates.get('front_motor_left',0.)+rates.get('front_motor_right',0.))/2
        # v2 couples active leg motors to pushing as well as contact. This is
        # a calibrated tool adapter, not learned anatomy or an added drive.
        push = motor/(15 if self.version == 3 else 25) if self.version >= 2 else 0.
        speed = float(np.tanh((forward-backward)/35 + push))
        heading = float((heading+turn*3*dt+np.pi)%(2*np.pi)-np.pi)
        lift = float(np.clip(escape/60,0,1))
        pressure = float(np.clip(motor/(6 if self.version >= 2 else 30),0,1))*(1-lift)
        steam = float(np.clip(motor/6 if self.version >= 2 else (motor-10)/30,0,1))
        action = np.array([np.cos(heading)*speed,np.sin(heading)*speed,pressure,steam])
        return action,heading,{'turn':turn,'speed':speed,'pressure':pressure,'steam':steam,'escape_lift':lift,
                               'version':self.version,
                               'method':'Fixed neural/tool adapter; no learned weights and no direct sensory-to-action bypass.'}
