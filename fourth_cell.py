
import random

HYPERRANGE_MAX = 100


class Fourth_cell:
    def __init__(self,stream,label):
        #initialisation
        self.stream = stream
        self.label = label
        self.fuzz = 0.00001
        self.mini = 10
        self.maxi = -10
        self.cur_mini = 10
        self.cur_maxi = -10
        self.u = 0
        self.v = 0
        self.VIGILANCE = 0.01

    def g(self ,s ,f ) :
        sy = s*f
        if sy > 1:
            #print(1)
            return 1
        elif sy >= 0 and sy <=1:
            #print(sy)
            return sy
        else: 
            #print(0)
            return 0


    def update(self, u, v, val):
        self.u = u
        self.v = v
        
        #print(u,v,self.mini,self.maxi)
        if self.mini > val:
            self.cur_mini = val

        if self.maxi < val:
            self.cur_maxi = val



    def downward_flow_in(self, val, uv_pair):
        u = uv_pair[0]
        v = uv_pair[1]

        self.update(u,v,val)

        f= self.fuzz
        z = 1 - self.g( val- v,f) - self.g(u-val,f)
        #print(uv_pair, f)
        #print('val,z:', val, z)
        
        return z

    def get_uv(self):
        return self.u, self.v

    def get_mid_simple(self):
        ans = (self.u + self.v) / 2
        return float("{:.2f}".format(ans))

    def get_cur_maxi(self):
        return self.cur_maxi

    def learn(self ,val, uv_pair):
        mini = self.mini
        maxi = self.maxi

        #update the mini and maxi if it changed
        if val< mini:
            mini = val
            self.mini = mini
        if val> maxi:
            maxi = val
            self.maxi = maxi

        u = uv_pair[0]
        v = uv_pair[1]

        #print(maxi, v,u,mini)
        #ans = ((maxi - v)+(u-mini))/2
        
        #self.fuzz =ans 

        self.fuzz = max((v-u),0.00001) / (self.VIGILANCE * max(abs(mini), maxi))

    def get_mid(self):
        mid = (self.u + self.v) / 2
        return mid
