unlockBinding("packageName", as.environment("package:utils"))

# Globally overwrite the function
assign("packageName",
       function() "myPatchedPackageName",
       pos = "package:utils")

