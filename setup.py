from setuptools import setup

with open("README.md", "r") as f:
    long_description = f.read()

long_description = long_description.replace('resources/demo_2x_speed.gif', 'https://github.com/jtc1246/openai-playground/blob/main/resources/demo_2x_speed.gif?raw=true')

setup(
    name='openai-playground',
    version='1.0.1',
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
