plugins {
    id("com.android.application")
}

// CI sets these; local builds fall back to the defaults below and the debug key
val keystoreFile: String? = System.getenv("ICONPACK_KEYSTORE")

android {
    namespace = "com.sabari.gruvboxclean"
    compileSdk = 36

    defaultConfig {
        applicationId = "com.sabari.gruvboxclean"
        minSdk = 26
        targetSdk = 36
        versionCode = System.getenv("ICONPACK_VERSION_CODE")?.toInt() ?: 2
        versionName = System.getenv("ICONPACK_VERSION_NAME") ?: "0.2.0"
    }

    signingConfigs {
        if (keystoreFile != null) {
            create("release") {
                storeFile = file(keystoreFile)
                storePassword = System.getenv("ICONPACK_KEYSTORE_PASSWORD")
                keyAlias = System.getenv("ICONPACK_KEY_ALIAS")
                keyPassword = System.getenv("ICONPACK_KEY_PASSWORD")
            }
        }
    }

    buildTypes {
        release {
            // Icons are looked up by name from XML, so the shrinker must not touch resources
            isMinifyEnabled = false
            isShrinkResources = false
            signingConfig = signingConfigs.getByName(if (keystoreFile != null) "release" else "debug")
        }
    }

    compileOptions {
        sourceCompatibility = JavaVersion.VERSION_17
        targetCompatibility = JavaVersion.VERSION_17
    }
}
