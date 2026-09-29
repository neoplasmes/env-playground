use crate::core::entities::Transformation;

pub fn validate_transformation(value: &Transformation) -> Result<(), &'static str> {
    if !(1..=4096).contains(&value.width) || !(1..=4096).contains(&value.height) {
        return Err("Dimensions must be between 1 and 4096");
    }
    if !["png", "jpeg", "webp"].contains(&value.format.as_str()) {
        return Err("Supported output formats: png, jpeg, webp");
    }
    Ok(())
}
