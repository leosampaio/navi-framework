from setuptools import find_packages, setup

setup(name='navi',
      version='0.1',
      py_modules=['navi'],
      author='Leonardo Sampaio Ferraz Ribeiro',
      author_email='leo.sampaio.ferraz.ribeiro@gmail.com',
      license='BSD',
      description=("A framework for quickly building better"
                   "and open personal assistants"),
      keywords="navi assistant bot chatbot framework",
      url="https://github.com/leosampaio/navi-framework",
      zip_safe=False,
      install_requires=['enum34==1.1.6', 'future==0.16.0', 'PyAudio==0.2.11',
                        'PyDispatcher==2.0.5', 'pyparsing==2.2.0',
                        'python-telegram-bot==5.3.1', 'pyttsx==1.1',
                        'requests==2.13.0', 'six==1.10.0', 'snowboy==1.2',
                        'SpeechRecognition==3.6.5', 'urllib3==1.20',
                        'wit==4.2.0'],
      )
