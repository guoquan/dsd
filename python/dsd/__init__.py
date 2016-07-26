from dsd.ui.web import app

class DSD(object):
    @classmethod
    def start(cls, dev=False, *args, **kwargs):
        if dev:
            app.run(host='0.0.0.0',
                    debug=dev,
                    *args, **kwargs)
        else:
            # TODO we should limit the host to be visit on running environment
            #app.run(host='localhost')
            app.run(host='0.0.0.0',
                    *args, **kwargs)
