plugins {
    id("com.android.application")
}

android {
    namespace = "com.sabari.gruvboxclean"
    compileSdk = 36

    defaultConfig {
        applicationId = "com.sabari.gruvboxclean"
        minSdk = 26
        targetSdk = 36
        versionCode = 2
        versionName = "0.2.0"
    }

    buildTypes {
        release {
            // Icons are looked up by name from XML, so the shrinker must not touch resources
            isMinifyEnabled = false
            isShrinkResources = false
        }
    }

    compileOptions {
        sourceCompatibility = JavaVersion.VERSION_17
        targetCompatibility = JavaVersion.VERSION_17
    }
}
