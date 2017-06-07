from setuptools import find_packages, setup

setup(name='navi',
      version='0.1.0a19',
      packages=find_packages(),
      author='Leonardo Sampaio Ferraz Ribeiro',
      author_email='leo.sampaio.ferraz.ribeiro@gmail.com',
      license='BSD',
      description=("A framework for quickly building better "
                   "and open personal assistants"),
      keywords="navi assistant bot chatbot framework",
      url="https://github.com/leosampaio/navi-framework",
      zip_safe=False,
      package_data={'': ['README.rst', 'LICENSE.txt', 'templates/*.tpl',
                         'resources/sounds/*.wav']},
      data_files=[('.', ['README.rst', 'LICENSE.txt']),
                  ('navi/resources/sounds', ['navi/resources/sounds/ding.wav',
                                             'navi/resources/sounds/dong.wav',
                                             ])],
      entry_points={
          'console_scripts': ['navi-create=navi.commands:navi_create_command'],
      },
      install_requires=[
          'enum34==1.1.6',
          'PyDispatcher==2.0.5'],
      extras_require={
          'SpeechRecognition':  [
              "PyAudio==0.2.11",
              "SpeechRecognition==3.6.5"],
          'HotwordDetection': [
              "PyAudio==0.2.11",
              "snowboy"],
          'Telegram': ["python-telegram-bot==5.3.1"],
          'Wit': ["wit==4.2.0"]}
      )
