use embuild::espidf::*;

fn main() -> anyhow::Result<()> {
    EspIdfBuildConfig::new().build()
}
