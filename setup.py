from setuptools import setup

with open("README.md", "r") as f:
    long_description = f.read()

long_description = long_description.replace('resources/demo_2x_speed.gif', 'https://github.com/jtc1246/openai-playground/blob/main/resources/demo_2x_speed.gif?raw=true')
long_description = long_description.replace('resources/chrome_extension.png', 'https://github.com/jtc1246/openai-playground/blob/main/resources/chrome_extension.png?raw=true')
long_description = long_description.replace('resources/extension_page.png', 'https://github.com/jtc1246/openai-playground/blob/main/resources/extension_page.png?raw=true')
long_description = long_description.replace('Demo:', "Demo: (if you can't see, go to [github.com/jtc1246/openai-playground](https://github.com/jtc1246/openai-playground))")
long_description = long_description.replace('(example.py)', ('(https://github.com/jtc1246/openai-playground/blob/main/example.py)'))

setup(
    name='openai-playground',
    version='1.0.3',
    author='Tiancheng Jiao',
    author_email='jtc1246@outlook.com',
    url='https://github.com/jtc1246/openai-playground',
    description='Use other openai-compatible API services in OpenAI Playground.',
    long_description=long_description,
    long_description_content_type="text/markdown",
    packages=['openai_playground'],
    package_data={
        'openai_playground': ['*.js']
    },
    install_requires=['mySecrets', 'myHttp', 'requests'],
    python_requires='>=3.9',
    platforms=["all"],
    license='GPL-2.0 License'
)
