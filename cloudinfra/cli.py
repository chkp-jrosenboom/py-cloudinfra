import cloudinfra
import click

@click.group()
def cli():
    pass

def complete_profile_names(ctx, param, incomplete):
    return [k for k in sorted(cloudinfra.configuration.list_profiles()) if k.startswith(incomplete)]

@cli.command()
@click.argument("profile_name", required=False, shell_complete=complete_profile_names)
def export(profile_name):

    if profile_name:
        config = cloudinfra.configuration.FileConfigProvider(profile_name=profile_name).load()
    else:
        config = cloudinfra.configuration.load_default()

    print(f" export CLOUDINFRA_APP={config.APP}")
    print(f" export CLOUDINFRA_KEY={config.KEY}")
    print(f" export CLOUDINFRA_SECRET={config.SECRET}")
    print(f" export CLOUDINFRA_URL={config.BASE_URL}")

@cli.command()
def list():
    for profile in sorted(cloudinfra.configuration.list_profiles()):
        if profile != "default":
            print(profile)
