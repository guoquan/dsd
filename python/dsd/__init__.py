from dsd.ui.web import app

class DSD(object):
    @classmethod
    def __call__(cls, dev=False, *args,**kwargs):
        return cls.start(dev, *args,**kwargs)

    @classmethod
    def start(cls, dev=False):
        if dev:
            app.run(host='0.0.0.0',
                    debug=dev)
        else:
            #app.run(host='localhost')
            app.run(host='0.0.0.0')
